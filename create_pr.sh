cd ~/repos/browser-use

cat > /tmp/PR_DESCRIPTION.md << EOL

This PR enhances the browser-use library to support photo selection and category navigation in Naver Maps restaurant listings. It focuses on improving iframe traversal and photo element detection.

- Fixed time_execution_async import in utils/__init__.py
- Enhanced find_naver_maps_photos_frame to include pcmap.place.naver.com frames
- Improved cross-origin iframe handling for Korean text detection
- Added dedicated method for finding and clicking Naver Maps photos
- Added category selection support

- Verified with Naver Maps restaurant URL provided by user
- Tested photo selection and category navigation
- Added screenshots for verification

https://app.devin.ai/sessions/4d8356242a504cc586fbc1e37cb1f407

Requested by: Al Tsang
EOL

git add browser_use/utils/__init__.py
git add browser_use/browser/context.py
git add examples/naver_restaurant_photo_test.py

git commit -m "Enhance Naver Maps photo navigation capabilities"

BRANCH_NAME=$(git branch --show-current)
git push -u origin $BRANCH_NAME
gh pr create --title "Enhance Naver Maps photo navigation capabilities" --body-file /tmp/PR_DESCRIPTION.md
