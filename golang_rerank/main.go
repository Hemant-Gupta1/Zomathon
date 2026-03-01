package main

import (
	"context"
	"log"
	"net"
	"os"

	"google.golang.org/grpc"
	"github.com/go-redis/redis/v8"
	"zomathon/titan/golang_rerank/rules"
)

// In a real project, this would be generated from a .proto file
type RankerServer struct{}

var rdb *redis.Client
var ctx = context.Background()

func main() {
	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		redisURL = "localhost:6379"
	}
	rdb = redis.NewClient(&redis.Options{
		Addr: redisURL,
	})

	listener, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	
	s := grpc.NewServer()
	// proto.RegisterRankerServer(s, &RankerServer{})

	log.Printf("GoLang Re-Ranker listening on :50051 (Budget: 20ms)")
	if err := s.Serve(listener); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}

// Pseudo-RPC handler
func ApplyRules(ctx context.Context, req map[string]interface{}) []string {
    // 20ms total budget 
    cartValue := req["cart_value"].(float64)
    userID := req["user_id"].(string)
    candidates := req["candidates"].([]string)

    // 1. Redis Bloom Filter check (Rejection Feedback)
    candidates = rules.FilterBloomRejections(ctx, rdb, userID, candidates)

    // 2. Price Anchoring 
    candidates = rules.ApplyPriceAnchoring(candidates, cartValue)

    // 3. Logistics Proximity (Google Routes API)
    candidates = rules.FilterProximity(candidates)
    
    // 4. Hyper-Local GeoSpecifics (Geohash check)
    candidates = rules.ApplyGeohash(candidates)

    // Apply strict final truncation
    if len(candidates) > 5 {
        return candidates[:5]
    }
    return candidates
}
