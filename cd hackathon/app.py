
from flask import Flask, render_template, request, jsonify
from profiler import compare_programs

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/compare", methods=["POST"])
def compare():
    data = request.get_json()
    source = data.get("source", "")

    if not source.strip():
        return jsonify({"error": "Please enter a program"}), 400

    try:
        result = compare_programs(source)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
