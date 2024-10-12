package main

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"sync"
	"time"

	ynisonGrpc "github.com/bulatorr/go-yaynison/ynison_grpc"
	ynisonstate "github.com/bulatorr/go-yaynison/ynisonstate"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials"
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

func generateTLSCreds() (credentials.TransportCredentials, error) {
	rootCAs, err := x509.SystemCertPool()
	if err != nil {
		return nil, fmt.Errorf("failed to get system cert pool: %v", err)
	}

	return credentials.NewTLS(&tls.Config{
		RootCAs: rootCAs,
	}), nil
}

func getSessionIdFromMd(md metadata.MD) string {
	sessionID := "UNKNOWN"
	if sessionIDs := md.Get("ynison-session-id"); len(sessionIDs) > 0 {
		sessionID = sessionIDs[0]
	}
	return sessionID
}

func (s *proxyServer) PutYnisonState(stream ynisonstate.YnisonStateService_PutYnisonStateServer) error {
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

	in, err := stream.Recv()
	if err != nil {
		logWithSessionID(sessionID, fmt.Sprintf("Error receiving initial message: %v", err))
		return status.Errorf(codes.InvalidArgument, "invalid entry message")
	}

	var wg_out sync.WaitGroup
	wg_out.Add(1)
	conn := new(ynisonGrpc.Conn)

	conn.OnMessage(func(response *ynisonstate.PutYnisonStateResponse) {
		if err := stream.Send(response); err != nil {
			logWithSessionID(sessionID, fmt.Sprintf("Error sending response to client: %v", err))
		}
		wg_out.Done()
	})

	conn.OnConnect(func() {
		logWithSessionID(sessionID, fmt.Sprintf("Connected to proxy host: %s", proxyHost[0]))
		err = conn.Send(in)
		if err != nil {
			logWithSessionID(sessionID, fmt.Sprintf("Error sending initial message within onConnect: %v", err))
		}
	})

	err = conn.Connect(proxyHost[0], headers)
	if err != nil {
		logWithSessionID(sessionID, fmt.Sprintf("Error connecting to destination: %v", err))
		return status.Errorf(codes.InvalidArgument, "unable to connect to dst")
	}
	defer conn.Close()

	var wg_in sync.WaitGroup
	wg_in.Add(1)

	go func() {
		defer wg_in.Done()
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
			wg_out.Add(1)
			if err := conn.Send(in); err != nil {
				logWithSessionID(sessionID, fmt.Sprintf("Error sending to proxy: %v", err))
				return
			}
		}
	}()

	wg_in.Wait()
	wg_out.Wait()
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
