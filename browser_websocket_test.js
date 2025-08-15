// Browser WebSocket Test (paste in browser console)
const ws = new WebSocket('ws://localhost:8000/ws/emotions?token=dev_ingest_token_please_change');

ws.onopen = function(event) {
    console.log('WebSocket connected!');
    
    // Send test emotion data
    const testData = {
        user_id: 1,
        emotion_label: "joy",
        valence: 0.8,
        arousal: 0.6,
        confidence: 0.9,
        source: "browser_test",
        raw_payload: { test: "data" }
    };
    
    ws.send(JSON.stringify(testData));
    console.log('Sent:', testData);
};

ws.onmessage = function(event) {
    console.log('Received:', event.data);
};

ws.onerror = function(error) {
    console.log('WebSocket error:', error);
};

ws.onclose = function(event) {
    console.log('WebSocket closed:', event.code, event.reason);
};
