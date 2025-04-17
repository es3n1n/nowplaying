FROM golang:1.23.8-alpine3.20 AS build

# Update packages and clear cache
RUN apk update && apk add --no-cache curl && rm -rf /var/cache/apk/*

# Set work directory
WORKDIR /app

# Create binary directory
RUN mkdir /app/bin -p

# Add main files to app
ADD . .

# Download go dependencies
RUN go mod download

# Build app
RUN CGO_ENABLED=0 go build -o bin/app ./main.go

FROM alpine:3.19 AS app

# Install packages
RUN apk --no-cache add ca-certificates && rm -rf /var/cache/apk/*

WORKDIR /app
COPY --from=build /app/bin/app ./app

CMD ["./app"]
