import React, { useState, useEffect, useMemo } from 'react';

interface HighlightedTextProps {
  text: string;
  keywords: string[];
  highlightEnabled: boolean;
}

const HighlightedText: React.FC<HighlightedTextProps> = ({ 
  text, 
  keywords, 
  highlightEnabled
}) => {
  // Use memoization to avoid recalculating on every render
  const processedText = useMemo(() => {
    if (!text) {
      return [];
    }

    if (!highlightEnabled || !keywords || keywords.length === 0) {
      return [text];
    }

    // Sort keywords by length (longest first) to prevent partial matches
    const sortedKeywords = [...keywords].sort((a, b) => b.length - a.length);

    let result: React.ReactNode[] = [];
    let lastIndex = 0;

    try {
      // Create regex pattern for all keywords with word boundaries
      // Filter out any empty keywords or invalid regex patterns
      const validKeywords = sortedKeywords
        .filter(k => k && k.trim().length > 0)
        .map(k => k.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'));
        
      if (validKeywords.length === 0) {
        return [text];
      }
        
      const keywordPattern = new RegExp(
        `\\b(${validKeywords.join('|')})\\b`, 
        'gi'
      );

      // Find all matches
      let match;
      let safetyCounter = 0; 
      const MAX_ITERATIONS = 1000; // Prevent infinite loops
      
      while ((match = keywordPattern.exec(text)) !== null && safetyCounter < MAX_ITERATIONS) {
        const matchedKeyword = match[0];
        const startIndex = match.index;
        
        // Add text before the match
        if (startIndex > lastIndex) {
          result.push(text.substring(lastIndex, startIndex));
        }
        
        // Add highlighted match
        result.push(
          <mark 
            key={`highlight-${startIndex}`} 
            className="bg-yellow-200 dark:bg-yellow-700 px-1 rounded"
          >
            {matchedKeyword}
          </mark>
        );
        
        lastIndex = startIndex + matchedKeyword.length;
        safetyCounter++;
      }
      
      // Add remaining text
      if (lastIndex < text.length) {
        result.push(text.substring(lastIndex));
      }
      
      return result;
    } catch (error) {
      console.error('Error highlighting text:', error);
      // Return unhighlighted text in case of errors
      return [text];
    }
  }, [text, keywords, highlightEnabled]);

  return <>{processedText}</>;
};

// Memoize the component to prevent unnecessary re-renders
export default React.memo(HighlightedText); 