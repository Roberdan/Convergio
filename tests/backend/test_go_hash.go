package main

import (
	"fmt"
	"golang.org/x/crypto/bcrypt"
	"log"
)

func main() {
	password := "admin123"
	storedHash := "$2a$12$LQv3c1yqBw2LHKVqY9nA0eBHhcrZWPh/lqwk0Lbt8u4cHj.JqKmFa"

	fmt.Printf("Testing password: %s\n", password)
	fmt.Printf("Against hash: %s\n", storedHash)

	// Test with Go bcrypt
	err := bcrypt.CompareHashAndPassword([]byte(storedHash), []byte(password))
	if err != nil {
		fmt.Printf("Go bcrypt result: ❌ No match (%v)\n", err)
	} else {
		fmt.Printf("Go bcrypt result: ✅ MATCH\n")
	}

	// Generate a new hash for comparison
	fmt.Println("\nGenerating new hash with Go bcrypt:")
	newHash, err := bcrypt.GenerateFromPassword([]byte(password), 12)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("New hash: %s\n", string(newHash))

	// Test the new hash
	err = bcrypt.CompareHashAndPassword(newHash, []byte(password))
	if err != nil {
		fmt.Printf("New hash verification: ❌ No match (%v)\n", err)
	} else {
		fmt.Printf("New hash verification: ✅ MATCH\n")
	}
}