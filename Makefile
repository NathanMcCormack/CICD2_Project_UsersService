UserServiceAPP = app.main:app 
install: 
	pip install -r requirements.txt 

runUsers: 
	python -m uvicorn $(UserServiceAPP) --host 0.0.0.0 --port 8000 --reload 

test: 
	python -m pytest -q
