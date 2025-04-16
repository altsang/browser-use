TIMESTAMP=$(date +%s)
BRANCH_NAME="devin/${TIMESTAMP}-enhanced-naver-photos"

git checkout main
git pull
git checkout -b $BRANCH_NAME

echo "Created branch $BRANCH_NAME"
