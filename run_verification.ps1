Write-Output "--- STAGE 3.6 FINAL VERIFICATION ---"

Write-Output "Running pytest backend/tests/ -q"
pytest backend/tests/ -q
$backend_code = $LASTEXITCODE
Write-Output "PYTEST_BACKEND_EXIT_CODE=$backend_code"

Write-Output "Running pytest backend/tests/api/test_gate15_5_scenarios.py -q"
pytest backend/tests/api/test_gate15_5_scenarios.py -q
$gate155_code = $LASTEXITCODE
Write-Output "PYTEST_GATE155_EXIT_CODE=$gate155_code"

Write-Output "Running pytest backend/tests/api/test_gate15_6_security.py -q"
pytest backend/tests/api/test_gate15_6_security.py -q
$gate156_code = $LASTEXITCODE
Write-Output "PYTEST_GATE156_EXIT_CODE=$gate156_code"

Push-Location frontend
Write-Output "Running npx vitest run"
npx vitest run
$vitest_code = $LASTEXITCODE
Write-Output "VITEST_EXIT_CODE=$vitest_code"

Write-Output "Running npm run build"
npm run build
$build_code = $LASTEXITCODE
Write-Output "BUILD_EXIT_CODE=$build_code"
Pop-Location

Write-Output "Running python scripts/demo_smoke_test.py"
python scripts/demo_smoke_test.py
$smoke_code = $LASTEXITCODE
Write-Output "SMOKE_EXIT_CODE=$smoke_code"

Write-Output "--- DONE ---"
