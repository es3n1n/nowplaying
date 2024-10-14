package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"strconv"
	"sync"
	"time"

	ynisonGrpc "github.com/bulatorr/go-yaynison/ynison_grpc"
	ynisonstate "github.com/bulatorr/go-yaynison/ynisonstate"
	"golang.org/x/sync/semaphore"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

const (
	proxyAddr = ":50051"
)

var (
	consoleLogger *log.Logger
)

type proxyServer struct {
	ynisonstate.UnimplementedYnisonStateServiceServer
}

func init() {
	multiWriter := io.Writer(os.Stdout)
	consoleLogger = log.New(multiWriter, "", log.Ldate|log.Ltime|log.Lshortfile)
}

func logWithSessionID(sessionID, message string) {
	prefix := fmt.Sprintf("[Session: %s] ", sessionID)
	consoleLogger.Println(prefix + message)
}

func getSessionIdFromMd(md metadata.MD) string {
	sessionID := "UNKNOWN"
	if sessionIDs := md.Get("ynison-session-id"); len(sessionIDs) > 0 {
		sessionID = sessionIDs[0]
	}
	return sessionID
}

func (s *proxyServer) PutYnisonState(stream ynisonstate.YnisonStateService_PutYnisonStateServer) error {
	const danglingMessagesCount = 10

	md, ok := metadata.FromIncomingContext(stream.Context())
	if !ok {
		logWithSessionID("UNKNOWN", "Error: Missing metadata")
		return status.Errorf(codes.InvalidArgument, "missing metadata")
	}

	sessionID := getSessionIdFromMd(md)
	logWithSessionID(sessionID, "Starting PutYnisonState stream")
	defer logWithSessionID(sessionID, "Ending PutYnisonState stream")

	proxyHost := md.Get("x-proxy-host")
	if len(proxyHost) == 0 {
		logWithSessionID(sessionID, "Error: Missing x-proxy-host in metadata")
		return status.Errorf(codes.InvalidArgument, "missing x-proxy-host in metadata")
	}

	logWithSessionID(sessionID, fmt.Sprintf("Routed to %s", proxyHost[0]))

	headers := make(map[string]string)
	for _, to_add := range []string{
		"authorization", "ynison-device-id", "ynison-session-id", "ynison-redirect-ticket",
	} {
		if values := md.Get(to_add); len(values) > 0 {
			headers[to_add] = values[0]
		} else {
			logWithSessionID(sessionID, fmt.Sprintf("Warning: Missing %s in metadata", to_add))
		}
	}

	wg_out := semaphore.NewWeighted(danglingMessagesCount)
	conn := new(ynisonGrpc.Conn)

	conn.OnMessage(
		func(response *ynisonstate.PutYnisonStateResponse) {
			if err := stream.Send(response); err != nil {
				logWithSessionID(sessionID, fmt.Sprintf("Error sending response to client: %v", err))
			}
			wg_out.Release(1)
		},
	)

	connectSignaler := make(chan struct{})
	conn.OnConnect(
		func() {
			connectSignaler <- struct{}{}
			close(connectSignaler)
		},
	)

	if err := conn.Connect(proxyHost[0], headers); err != nil {
		logWithSessionID(sessionID, fmt.Sprintf("Error connecting to destination: %v", err))
		return status.Errorf(codes.InvalidArgument, "unable to connect to dst")
	}
	defer conn.Close()

	var wg_in sync.WaitGroup
	wg_in.Add(1)
	ctx := context.Background()
	isTimedOut := false

	timeout := 30
	if proxyTimeout := md.Get("x-proxy-timeout"); len(proxyTimeout) > 0 {
		n, err := strconv.Atoi(proxyTimeout[0])

		if err != nil {
			return fmt.Errorf("invalid timeout value: %w", err)
		}

		timeout = n
	}

	go func() {
		defer wg_in.Done()

		timer := time.NewTimer(time.Duration(timeout) * time.Second)

		select {
		case <-timer.C:
			return
		case <-connectSignaler:
			logWithSessionID(sessionID, "Connected to the ynison server")
		}

		for {
			in, err := stream.Recv()
			if err == io.EOF {
				logWithSessionID(sessionID, "Client stream ended")
				return
			}
			if err != nil {
				logWithSessionID(sessionID, fmt.Sprintf("Error receiving from client: %v", err))
				return
			}
			logWithSessionID(sessionID, fmt.Sprintf("Received message from client: %v", in))

			timedCtx, cancel := context.WithTimeout(ctx, time.Duration(timeout)*time.Second)
			if err := wg_out.Acquire(timedCtx, 1); err != nil {
				isTimedOut = true
				cancel()
				logWithSessionID(sessionID, fmt.Sprintf("error acquiring semaphore: %v", err))
				return
			}
			cancel()

			if err := conn.Send(in); err != nil {
				logWithSessionID(sessionID, fmt.Sprintf("Error sending to proxy: %v", err))
				return
			}
		}
	}()

	wg_in.Wait()

	if !isTimedOut {
		timedCtx, cancel := context.WithTimeout(ctx, time.Duration(timeout)*time.Second)
		defer cancel()
		_ = wg_out.Acquire(timedCtx, danglingMessagesCount)
	}

	return nil
}

func main() {
	logWithSessionID("MAIN", "Starting proxy server")

	lis, err := net.Listen("tcp", proxyAddr)
	if err != nil {
		logWithSessionID("MAIN", fmt.Sprintf("Failed to listen: %v", err))
		os.Exit(1)
	}

	s := grpc.NewServer(
		grpc.StreamInterceptor(streamInterceptor),
	)

	ynisonstate.RegisterYnisonStateServiceServer(s, &proxyServer{})
	logWithSessionID("MAIN", fmt.Sprintf("Server listening at %v", lis.Addr()))

	if err := s.Serve(lis); err != nil {
		logWithSessionID("MAIN", fmt.Sprintf("Failed to serve: %v", err))
		os.Exit(1)
	}
}

func streamInterceptor(srv interface{}, ss grpc.ServerStream, info *grpc.StreamServerInfo, handler grpc.StreamHandler) error {
	start := time.Now()
	err := handler(srv, ss)

	md, ok := metadata.FromIncomingContext(ss.Context())
	sessionID := "UNKNOWN"
	if ok {
		sessionID = getSessionIdFromMd(md)
	}

	logWithSessionID(sessionID, fmt.Sprintf("Stream RPC: %s, Duration: %s, Error: %v", info.FullMethod, time.Since(start), err))
	return err
}
