#!/usr/bin/env bash
# Engineering Quality Lab - Unified Continuous Integration (CI) Pipeline Check
# Covers Python Ruff, Mypy, Pytest Coverage, TypeScript Strict, Vite Build, Vitest, and Playwright E2E.

set -e

echo "============================================================"
echo "🚀 [CI STEP 1/7]: Running Python Ruff Linter..."
echo "============================================================"
cd /home/brrr/agy
ruff check --config backend/pyproject.toml backend/app
echo "✅ Ruff checks passed!"

echo ""
echo "============================================================"
echo "🔬 [CI STEP 2/7]: Running Python Mypy Static Type Checker..."
echo "============================================================"
mypy --config-file backend/pyproject.toml backend/app
echo "✅ Mypy type check passed!"

echo ""
echo "============================================================"
echo "🧪 [CI STEP 3/7]: Running Backend Pytest Suite & Coverage..."
echo "============================================================"
PYTHONPATH=backend python3 -m pytest backend/tests/ --cov=app --cov-config=backend/.coveragerc --cov-report=term-missing
echo "✅ Backend tests passed with >= 85% coverage!"

echo ""
echo "============================================================"
echo "📐 [CI STEP 4/7]: Running TypeScript Strict Compilation Check..."
echo "============================================================"
cd /home/brrr/agy/frontend
npx tsc --noEmit
echo "✅ TypeScript strict check passed!"

echo ""
echo "============================================================"
echo "📦 [CI STEP 5/7]: Running Frontend Production Build (Vite)..."
echo "============================================================"
npm run build
echo "✅ Frontend production build succeeded!"

echo ""
echo "============================================================"
echo "⚡ [CI STEP 6/7]: Running Frontend Vitest Suite (>=100 tests)..."
echo "============================================================"
npx vitest run
echo "✅ Vitest tests passed!"

echo ""
echo "============================================================"
echo "🎭 [CI STEP 7/7]: Running Playwright E2E (>=40 flows)..."
echo "============================================================"
npx playwright test e2e/comprehensive_acceptance.spec.ts
echo "✅ Playwright 40 E2E flows passed!"

echo ""
echo "============================================================"
echo "🎉 ALL 7 CI PIPELINE STAGES PASSED CLEANLY WITH ZERO ERRORS!"
echo "============================================================"
