if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  source venv/bin/activate
  flask run --debug
elif [[ "$OSTYPE" == "darwin"* ]]; then
  source venv/bin/activate
  flask run --debug
elif [[ "$OSTYPE" == "cygwin" ]]; then
  source venv/Scripts/activate
  flask run --debug
elif [[ "$OSTYPE" == "msys" ]]; then
  source venv/Scripts/activate
  flask run --debug
elif [[ "$OSTYPE" == "win32" ]]; then
  source venv/Scripts/activate
  flask run --debug
elif [[ "$OSTYPE" == "freebsd"* ]]; then
  source venv/bin/activate
  flask run --debug
else
  echo "Unknown OSTYPE"
fi