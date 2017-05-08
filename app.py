from flask import Flask, render_template, jsonify
from finance import Finances, Source, TransactionList

app = Flask(__name__)
app.finances = Finances()
app.finances.load_current_finances()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summary')
def summary():
	return app.finances.__repr__()

@app.route('/chase')
def chase():
	for s in app.finances.sources:
		if s.name == "chase":
			target_source = s
	monthly = target_source.monthly_summary()
	labels = []
	datapoints = []
	for year in monthly.keys():
		for month in monthly[year].keys():
			label = "%s/%s" % (month,year)
			datapoint = monthly[year][month]
			labels.append(label)
			datapoints.append(datapoint)
	print labels
	print datapoints
	res = {"labels":labels,"datapoints":datapoints}
	return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True)