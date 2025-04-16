

echo "Testing Agent-based approach for Naver Maps restaurant photos:"
echo "------------------------------------------------------------"
python examples/naver_agent_simple_final.py
EXIT_CODE=$?

echo ""
echo "Verification complete with exit code: $EXIT_CODE"
exit $EXIT_CODE
