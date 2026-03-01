package rules

func ApplyPriceAnchoring(candidates []string, cartValue float64) []string {
	var filtered []string
	
	// Max allowed price is max(50, cartValue * 0.4)
	maxAllowed := 50.0
	if dynamicMax := cartValue * 0.4; dynamicMax > 50.0 {
		maxAllowed = dynamicMax
	}
	
	// Assume a hypothetical lookup for item prices
	for _, item := range candidates {
		// Example price dummy logic
		itemPrice := GetItemPrice(item) 
		if itemPrice <= maxAllowed {
			filtered = append(filtered, item)
		}
	}
	
	return filtered
}

func GetItemPrice(itemID string) float64 {
	// Stub
	return 45.0
}
