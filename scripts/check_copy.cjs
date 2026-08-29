#!/usr/bin/env node
/**
 * FPL Dugout — Automated Frontend Voice, Tone & Copy Validator (Node.js)
 * 
 * Runs automatically before every Vite build (`npm run build`) and via `npm run check-copy`.
 * Enforces docs/voice-and-tone-guide.md standards.
 */

const fs = require('fs');
const path = require('path');

const BANNED_RULES = [
  {
    pattern: /\bassets?\b/i,
    category: 'Tier 3: Corporate Jargon',
    message: "Use 'player', 'squad', or 'picks' instead of 'asset/assets'.",
    suggestion: 'player / squad / picks',
    exemptCode: true,
  },
  {
    pattern: /\bportfolios?\b/i,
    category: 'Tier 3: Corporate Jargon',
    message: "Use 'squad' or 'team' instead of 'portfolio'.",
    suggestion: 'squad / team',
  },
  {
    pattern: /\bcapital\b(?!\s+(?:letter|city))/i,
    category: 'Tier 3: Corporate Jargon',
    message: "Use 'budget' or 'bank balance' instead of 'capital'.",
    suggestion: 'budget / bank balance',
  },
  {
    pattern: /\bfunds\s+depletion\b/i,
    category: 'Tier 3: Corporate Jargon',
    message: "Use 'extra cost' or 'not enough bank balance'.",
    suggestion: 'extra cost / bank balance',
  },
  {
    pattern: /\bdownside\s+(?:protection|risk)\b/i,
    category: 'Tier 3: Corporate Jargon',
    message: "Use 'protecting your lead' or 'safe template picks'.",
    suggestion: 'protecting your lead / safe picks',
  },
  {
    pattern: /\bexecution\s+error\b/i,
    category: 'Tier 3: Robotic Error',
    message: "Use 'Formation Alert' or 'Transfer Error'.",
    suggestion: 'Formation Alert / Transfer Error',
  },
  {
    pattern: /\bsub-?optimal\b/i,
    category: 'Tier 3: Robotic Jargon',
    message: "Use 'invalid squad' or 'lower-scoring pick'.",
    suggestion: 'invalid squad / lower-scoring pick',
  },
  {
    pattern: /\broster\s+composition\b/i,
    category: 'Tier 3: Robotic Jargon',
    message: "Use 'squad formation' or 'team lineup'.",
    suggestion: 'squad formation / team lineup',
  },
  {
    pattern: /\brisk\s+profile\b/i,
    category: 'Tier 3: Corporate Jargon',
    message: "Use 'play style' or 'tactical goal'.",
    suggestion: 'play style / tactical goal',
  },
  {
    pattern: /\bexpected\s+value\b/i,
    category: 'Tier 2: Statistical Term',
    message: "Translate to 'Expected Points', 'Exp Pts', or 'Projected Points'.",
    suggestion: 'Expected Points / Exp Pts',
  },
  {
    pattern: /\b(?:bivariate\s+)?dixon-?coles\b/i,
    category: 'Tier 2: Raw Model Name',
    message: "Translate to 'Match Preview' or 'Clean Sheet Odds'.",
    suggestion: 'Match Preview · Clean Sheet Odds',
  },
  {
    pattern: /\bpoisson\s+(?:distribution|model|pmf)\b/i,
    category: 'Tier 2: Raw Model Name',
    message: "Translate to 'Clean Sheet Chances' or 'Scoreline Odds'.",
    suggestion: 'Scoreline Chances & Clean Sheet Odds',
  },
  {
    pattern: /\b(?:empirical\s+)?bayesian\s+shrinkage\b/i,
    category: 'Tier 2: Raw Model Name',
    message: "Translate to 'Blending Recent Form with Career Record'.",
    suggestion: 'Blending Recent Form with Career Record',
  },
  {
    pattern: /\bmonopolizes?\b/i,
    category: 'Anti-Slop: Overstated Verb',
    message: "Use 'takes all corners/free-kicks' instead of 'monopolizes'.",
    suggestion: 'takes all / delivers all',
  },
  {
    pattern: /\bstands?\s+as\s+a\s+testament\b/i,
    category: 'Anti-Slop: AI Filler',
    message: 'Cut inflated phrasing; state the fact directly.',
    suggestion: 'shows / is',
  },
  {
    pattern: /\bdelivering\s+higher\s+baseline\s+security\b/i,
    category: 'Anti-Slop: Corporate Fluff',
    message: "Use 'safest pick' or 'reliable points floor'.",
    suggestion: 'safest pick / reliable points floor',
  },
  {
    pattern: /\bhere's\s+the\s+thing\b/i,
    category: 'Anti-Slop: Throat-Clearing',
    message: 'Cut throat-clearing and state the point directly.',
    suggestion: '[state point directly]',
  },
  {
    pattern: /\blet\s+that\s+sink\s+in\b/i,
    category: 'Anti-Slop: Emphasis Crutch',
    message: 'Cut emphasis crutch.',
    suggestion: '[remove phrase]',
  },
  {
    pattern: /\bseamlessly\b/i,
    category: 'Anti-Slop: Corporate Buzzword',
    message: "Cut 'seamlessly' or use 'easily/smoothly'.",
    suggestion: 'easily / smoothly',
  },
  {
    pattern: /\bleverage\s+(?:your|our|their|the)\b/i,
    category: 'Anti-Slop: Corporate Buzzword',
    message: "Use 'use' or 'take advantage of' instead of 'leverage'.",
    suggestion: 'use / back',
  },
];

function extractUserFacingStrings(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  const extracted = [];

  lines.forEach((line, index) => {
    const lineNum = index + 1;
    const stripped = line.trim();

    if (stripped.startsWith('//') || stripped.startsWith('/*') || stripped.startsWith('*')) return;
    if (stripped.startsWith('import ') || stripped.startsWith('import{')) return;

    // Remove className="..."
    const cleanedLine = line.replace(/className=(?:\{[^}]*\}|"[^"]*"|'[^']*')/g, '');

    // String literals
    const stringMatches = cleanedLine.match(/['"`]([^'"`\n]{3,})['"`]/g) || [];
    for (const match of stringMatches) {
      const s = match.slice(1, -1);
      if (s.startsWith('./') || s.startsWith('../') || s.startsWith('http') || s.startsWith('var(--') || s.startsWith('#') || s.startsWith('rgba')) continue;
      if (s.endsWith('.css') || s.endsWith('.js') || s.endsWith('.jsx') || s.endsWith('.json') || s.endsWith('.svg')) continue;
      if (/^[a-z0-9_]+$/.test(s) && !s.includes(' ')) continue;
      extracted.push({ lineNum, text: s, fullLine: line.trim() });
    }

    // JSX text children
    const jsxMatches = line.match(/>([^<>{}\n]{3,})</g) || [];
    for (const jm of jsxMatches) {
      const jt = jm.slice(1, -1).trim();
      if (jt) extracted.push({ lineNum, text: jt, fullLine: line.trim() });
    }
  });

  return extracted;
}

function scanDir(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      scanDir(fullPath, fileList);
    } else if (file.endsWith('.jsx') || file.endsWith('.js') || file.endsWith('.html')) {
      fileList.push(fullPath);
    }
  }
  return fileList;
}

function main() {
  const repoRoot = path.resolve(__dirname, '..');
  const frontendSrc = path.join(repoRoot, 'frontend', 'src');

  console.log('======================================================================');
  console.log('[INFO] FPL Dugout Voice, Tone & Copy Validator (Node.js)');
  console.log('       Enforcing docs/voice-and-tone-guide.md standards');
  console.log('======================================================================');

  const files = scanDir(frontendSrc);
  console.log(`Scanned ${files.length} frontend files across frontend/src\n`);

  const violations = [];

  for (const filePath of files) {
    const extracted = extractUserFacingStrings(filePath);
    for (const item of extracted) {
      for (const rule of BANNED_RULES) {
        const match = item.text.match(rule.pattern);
        if (match) {
          const matchedWord = match[0];
          if (rule.exemptCode) {
            if (item.fullLine.includes(`${matchedWord}_`) || item.fullLine.includes(`_${matchedWord}`) || item.fullLine.includes(`.${matchedWord}`)) {
              continue;
            }
            if (item.fullLine.includes('assets/') || item.fullLine.includes('/assets')) {
              continue;
            }
          }

          violations.push({
            file: path.relative(repoRoot, filePath).replace(/\\/g, '/'),
            line: item.lineNum,
            matched: matchedWord,
            category: rule.category,
            message: rule.message,
            suggestion: rule.suggestion,
            fullLine: item.fullLine,
          });
        }
      }
    }
  }

  if (violations.length > 0) {
    console.error(`[FAIL] Found ${violations.length} copy violation(s):\n`);
    const seen = new Set();
    for (const v of violations) {
      const key = `${v.file}:${v.line}:${v.matched}`;
      if (seen.has(key)) continue;
      seen.add(key);

      console.error(`  * ${v.file}:${v.line}`);
      console.error(`     Category:   ${v.category}`);
      console.error(`     Matched:    '${v.matched}'`);
      console.error(`     Line:       ${v.fullLine}`);
      console.error(`     Guidance:   ${v.message}`);
      console.error(`     Suggested:  ${v.suggestion}\n`);
    }
    console.error('======================================================================');
    console.error('Please fix the copy violations above or update docs/voice-and-tone-guide.md.');
    process.exit(1);
  } else {
    console.log('[PASS] All frontend copy conforms to the FPL Dugout Voice & Tone Guide.');
    console.log('       0 banned words or un-translated terms detected.\n');
    console.log('======================================================================');
    process.exit(0);
  }
}

main();
