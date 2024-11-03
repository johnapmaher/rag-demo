curl -X POST "https://0b25h7mp8a.execute-api.us-east-1.amazonaws.com/Prod/upload" \
     -H "file-name: large_story_demo_rag.txt" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@large_story_demo_rag.txt"

curl -X POST "http://localhost:3000/upload" \
     -H "file-name: large_story_demo_rag.txt" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@large_story_demo_rag.txt"