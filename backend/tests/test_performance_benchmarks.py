import sys, time, unittest
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from app.services import dataset_store, dataset_service, column_profiler, recommendation_engine


class TestPerformanceBenchmarks(unittest.TestCase):
    def test_small_dataset_performance(self):
        """Test with small dataset (150 rows)."""
        np.random.seed(42)
        n = 150
        dates = pd.date_range("2023-01-01", periods=30, freq="D")
        df_small = pd.DataFrame({
            "order_id": [f"ID_{i}" for i in range(n)],
            "date": np.random.choice(dates, n),
            "customer": np.random.choice(["Alice", "Bob", "Charlie", "David"], n),
            "category": np.random.choice(["Electronics", "Books", "Clothing"], n),
            "amount": np.random.uniform(10, 500, n),
            "profit": np.random.uniform(-50, 100, n),
        })

        ds_id = dataset_store.save_dataset("small.csv", "csv", df_small)

        t0 = time.perf_counter()
        recs = dataset_service.get_recommendations(ds_id)
        t_recs = time.perf_counter() - t0
        self.assertLess(t_recs, 0.5, f"Small recommendations too slow: {t_recs:.4f}s")

        t0 = time.perf_counter()
        intel = dataset_service.get_domain_intelligence(ds_id)
        t_intel = time.perf_counter() - t0
        self.assertLess(t_intel, 0.8, f"Small intelligence too slow: {t_intel:.4f}s")

        t0 = time.perf_counter()
        trends = dataset_service.get_trends_intelligence(ds_id)
        t_trends = time.perf_counter() - t0
        self.assertLess(t_trends, 0.5, f"Small trends too slow: {t_trends:.4f}s")

    def test_large_dataset_performance_and_caching(self):
        """Test with large dataset (10,000 rows) and verify instant cache reuse."""
        np.random.seed(42)
        n = 10000
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        df_large = pd.DataFrame({
            "order_id": [f"ORD-{i}" for i in range(n)],
            "order_date": np.random.choice(dates, n),
            "customer_name": np.random.choice([f"Customer {i}" for i in range(50)], n),
            "category": np.random.choice(["Electronics", "Furniture", "Clothing", "Office Supplies", "Toys"], n),
            "region": np.random.choice(["North", "South", "East", "West", "Central"], n),
            "sales_amount": np.random.exponential(150, n) + 10,
            "profit": np.random.normal(25, 40, n),
            "quantity": np.random.randint(1, 15, n),
            "discount": np.random.choice([0.0, 0.05, 0.1, 0.2, 0.3], n),
            "shipping_cost": np.random.uniform(5, 50, n),
            "delivery_days": np.random.randint(1, 14, n),
        })

        ds_id = dataset_store.save_dataset("large_10k.csv", "csv", df_large)

        # 1. Cold execution on 10,000 rows
        t0 = time.perf_counter()
        recs_cold = dataset_service.get_recommendations(ds_id)
        t_recs_cold = time.perf_counter() - t0
        self.assertLess(t_recs_cold, 2.5, f"Cold recommendations on 10k rows took {t_recs_cold:.4f}s (expected < 2.5s)")

        t0 = time.perf_counter()
        intel_cold = dataset_service.get_domain_intelligence(ds_id)
        t_intel_cold = time.perf_counter() - t0
        self.assertLess(t_intel_cold, 2.5, f"Cold intelligence on 10k rows took {t_intel_cold:.4f}s (expected < 2.5s)")

        t0 = time.perf_counter()
        trends_cold = dataset_service.get_trends_intelligence(ds_id)
        t_trends_cold = time.perf_counter() - t0
        self.assertLess(t_trends_cold, 1.5, f"Cold trends on 10k rows took {t_trends_cold:.4f}s (expected < 1.5s)")

        # 2. Warm cached execution (navigation across tabs)
        t0 = time.perf_counter()
        recs_warm = dataset_service.get_recommendations(ds_id)
        t_recs_warm = time.perf_counter() - t0
        self.assertLess(t_recs_warm, 0.005, f"Warm cached recommendations took {t_recs_warm:.6f}s (expected < 5ms)")

        t0 = time.perf_counter()
        intel_warm = dataset_service.get_domain_intelligence(ds_id)
        t_intel_warm = time.perf_counter() - t0
        self.assertLess(t_intel_warm, 0.005, f"Warm cached intelligence took {t_intel_warm:.6f}s (expected < 5ms)")

        t0 = time.perf_counter()
        trends_warm = dataset_service.get_trends_intelligence(ds_id)
        t_trends_warm = time.perf_counter() - t0
        self.assertLess(t_trends_warm, 0.005, f"Warm cached trends took {t_trends_warm:.6f}s (expected < 5ms)")


if __name__ == "__main__":
    unittest.main()
