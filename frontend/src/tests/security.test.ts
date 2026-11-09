import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

function getAllFiles(dirPath: string, arrayOfFiles: string[] = []) {
  const files = fs.readdirSync(dirPath);

  files.forEach(function(file) {
    const fullPath = dirPath + "/" + file;
    if (fs.statSync(fullPath).isDirectory()) {
      arrayOfFiles = getAllFiles(fullPath, arrayOfFiles);
    } else {
      if (fullPath.endsWith('.ts') || fullPath.endsWith('.tsx')) {
        arrayOfFiles.push(fullPath);
      }
    }
  });

  return arrayOfFiles;
}

describe('Frontend Source Security Constraints', () => {
    it('ensures no literal raw PAN sequences exist in frontend source', () => {
        const files = getAllFiles(path.resolve(__dirname, '../'));
        let foundViolations = false;
        
        for (const file of files) {
            const content = fs.readFileSync(file, 'utf-8');
            // This tests that the specific PAN pattern requested to be removed is completely absent
            if (content.includes('41112222' + '33334444')) {
                foundViolations = true;
                console.error(`Violation in ${file}: Literal PAN found.`);
            }
        }
        
        expect(foundViolations).toBe(false);
    });

    it('ensures no direct use of localStorage, sessionStorage for potential leakage', () => {
        const files = getAllFiles(path.resolve(__dirname, '../'));
        let foundViolations = false;
        
        for (const file of files) {
            // Ignore the test file itself
            if (file.includes('security.test.ts')) continue;
            
            const content = fs.readFileSync(file, 'utf-8');
            if (content.includes('localStorage.setItem') || content.includes('sessionStorage.setItem')) {
                foundViolations = true;
                console.error(`Violation in ${file}: Browser persistence APIs used.`);
            }
            if (content.includes('console.log(payload)')) {
                foundViolations = true;
                console.error(`Violation in ${file}: console.log(payload) used.`);
            }
        }
        
        expect(foundViolations).toBe(false);
    });
});
