echo "Running Naver restaurant photo test..."
cd ~/repos/browser-use
python examples/naver_restaurant_photo_test.py

if [ $? -eq 0 ]; then
    echo "✅ Test passed!"
else
    echo "❌ Test failed!"
fi

echo "Opening screenshots for verification..."
ls -l /tmp/naver_test/
