package rules

func ApplyGeohash(candidates []string) []string {
	// Filter based on hyper-local geohash dictionary lookup
	// Drop items that are historically unsuccessful in this geohash
	return candidates
}

func FilterProximity(candidates []string) []string {
	// Stub to check if the recommended restaurant is within 500m of the active route using Google Routes API
	// e.g. CallGoogleRoutesAPI(activeRoute, candidateRestaurantLocation)
	return candidates
}
