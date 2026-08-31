package main

import (
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

const maxFileBytes int64 = 128 * 1024 * 1024

var markdownLinkPattern = regexp.MustCompile(`!?\[[^\]]*\]\(([^)\s]+)(?:\s+["'][^"']*["'])?\)`)

type auditReport struct {
	File        string   `json:"file"`
	Links       int      `json:"links"`
	LocalLinks  int      `json:"localLinks"`
	BrokenLinks []string `json:"brokenLinks"`
}

func defIsExternal(target string) bool {
	lower := strings.ToLower(target)
	return strings.HasPrefix(lower, "http://") || strings.HasPrefix(lower, "https://") ||
		strings.HasPrefix(lower, "mailto:") || strings.HasPrefix(lower, "tel:") ||
		strings.HasPrefix(lower, "data:") || strings.HasPrefix(lower, "#")
}

func defStripTarget(target string) string {
	withoutAnchor := strings.SplitN(target, "#", 2)[0]
	withoutQuery := strings.SplitN(withoutAnchor, "?", 2)[0]
	decoded, err := url.PathUnescape(withoutQuery)
	if err != nil {
		return withoutQuery
	}
	return decoded
}

func defAudit(input string) (auditReport, error) {
	info, err := os.Stat(input)
	if err != nil {
		return auditReport{}, err
	}
	if info.Size() > maxFileBytes {
		return auditReport{}, fmt.Errorf("file exceeds %d bytes", maxFileBytes)
	}
	content, err := os.ReadFile(input)
	if err != nil {
		return auditReport{}, err
	}
	report := auditReport{File: input, BrokenLinks: []string{}}
	matches := markdownLinkPattern.FindAllStringSubmatch(string(content), -1)
	report.Links = len(matches)
	for _, match := range matches {
		target := match[1]
		if defIsExternal(target) {
			continue
		}
		cleaned := defStripTarget(target)
		if cleaned == "" {
			continue
		}
		report.LocalLinks++
		candidate := filepath.Clean(filepath.Join(filepath.Dir(input), filepath.FromSlash(cleaned)))
		if _, err := os.Stat(candidate); err != nil {
			report.BrokenLinks = append(report.BrokenLinks, target)
		}
	}
	return report, nil
}

func defMain() int {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "Usage: mdlinkcheck <file.md>")
		return 2
	}
	report, err := defAudit(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 2
	}
	encoded, _ := json.Marshal(report)
	fmt.Println(string(encoded))
	if len(report.BrokenLinks) > 0 {
		return 1
	}
	return 0
}

func main() {
	os.Exit(defMain())
}
