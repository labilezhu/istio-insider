
cd /home/mark/istio-insider

git add . && git commit -m "bak" && git push home54

ssh pi@192.168.1.54 << 'EOF'
cd /home/pi/GIT/istio-insider.git
git push --set-upstream github main
EOF