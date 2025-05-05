from flask import Flask, request, jsonify
from toy_distance_module import haversine_distance

app = Flask(__name__)

@app.route('/distance', methods=['POST'])
def calculate_distance():
    data = request.get_json()
    lat1 = data.get('lat1')
    lon1 = data.get('lon1')
    lat2 = data.get('lat2')
    lon2 = data.get('lon2')

    # Validate input
    if None in [lat1, lon1, lat2, lon2]:
        return jsonify({'error': 'Missing coordinates'}), 400

    distance = haversine_distance(lat1, lon1, lat2, lon2)
    return jsonify({'distance_km': distance})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
