
db = db.getSiblingDB('valenbisi');

// Colección para datos históricos (Time Series)
db.createCollection("station_status", {
   timeseries: {
      timeField: "timestamp",
      metaField: "station_id",
      granularity: "minutes"
   }
});

// Colección para estado actual
db.createCollection("latest_status");

// Índices
db.station_status.createIndex({ "station_id": 1, "timestamp": -1 });
db.latest_status.createIndex({ "station_id": 1 }, { unique: true });
db.latest_status.createIndex({ "geo_point": "2dsphere" });

print("Valenbisi MongoDB Collections Initialized");
