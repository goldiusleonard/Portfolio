import numpy as np
import pandas as pd
import logging
from prophet import Prophet
from typing import Union


class EngagementAndRiskPrediction:
    def __init__(self, filtered_video_df, start_date, end_date):
        self.filtered_video_df = filtered_video_df
        self.start_date = start_date
        self.end_date = end_date

        self.metrics = {
            "engagement": ("total_video_engagement", "sum"),
            "risk": ("video_engagement_risk", "sum"),
        }

    def _process_group_data(self, group_data, metric_column, agg_func):
        """Processes data to prepare it for forecasting."""
        logging.info(f"Processing data for: {metric_column}")

        group_data["video_posted_timestamp"] = pd.to_datetime(
            group_data["video_posted_timestamp"], errors="coerce"
        )

        # Group by date and aggregate
        grouped_data = (
            group_data.groupby(group_data["video_posted_timestamp"].dt.date)
            .agg({metric_column: agg_func})
            .reset_index()
            .rename(columns={"video_posted_timestamp": "ds", metric_column: "y"})
        )
        return grouped_data

    def _transform_risk_status(self, group_data):
        """Encodes risk_status to numeric values and processes the data."""
        risk_mapping = {"low": 1, "medium": 2, "high": 3}

        # Convert risk_status to numerical values
        group_data["risk_status"] = group_data["risk_status"].map(risk_mapping)

        # Drop rows where risk_status couldn't be mapped
        group_data = group_data.dropna(subset=["risk_status"])

        grouped_data = self._process_group_data(group_data, "risk_status", "mean")
        return grouped_data, risk_mapping

    def _generate_forecasts(
        self, grouped_data: pd.DataFrame, metric, risk_mapping: Union[dict, None] = None
    ):
        """Generates forecasts using the Prophet model."""
        if grouped_data["y"].isnull().all() or grouped_data.shape[0] < 2:
            logging.info(f"Not enough data to generate forecast for metric: {metric}")
            return pd.DataFrame()

        num_changepoints = 5
        changepoints = grouped_data["ds"].quantile(
            np.linspace(0.1, 0.9, num_changepoints)
        )

        model = Prophet(
            growth="linear",
            changepoint_prior_scale=1.0,
            yearly_seasonality=False,
            seasonality_mode="multiplicative",
            seasonality_prior_scale=14,
            changepoints=changepoints,
            interval_width=0.95,
        )
        model.add_seasonality(name="weekly", period=7, fourier_order=5)
        model.add_seasonality(name="monthly", period=30.5, fourier_order=30)

        model.fit(grouped_data)

        # Generate future dates
        future_dates = pd.date_range(start=self.start_date, end=self.end_date)
        future = pd.DataFrame({"ds": future_dates})

        # Predict future values
        forecast = model.predict(future)

        # Modify predicted values to ensure they are not negative (no negative engagement)
        forecast["yhat"] = forecast["yhat"].clip(lower=0)
        forecast["yhat_lower"] = forecast["yhat_lower"].clip(lower=0)
        forecast["yhat_upper"] = forecast["yhat_upper"].clip(lower=0)

        # # Map risk_status predictions back to categories (if applicable)
        # if metric == "risk_status_predicted" and risk_mapping:
        #     forecast["Predicted Value"] = (
        #         forecast["yhat"].round().clip(1, 3)
        #     )  # Ensure values are between 1 and 3
        #     reverse_mapping = {v: k for k, v in risk_mapping.items()}
        #     forecast["Predicted Value"] = forecast["Predicted Value"].map(
        #         reverse_mapping
        #     )
        # else:
        forecast["Predicted Value"] = forecast["yhat"]

        # Finalize the forecast dataframe
        forecast["Metric"] = metric
        forecast.rename(columns={"ds": "Date"}, inplace=True)
        forecast["Date"] = pd.to_datetime(forecast["Date"])
        return forecast[["Date", "Predicted Value", "Metric"]]

    def predict(self):
        """Main prediction function that generates forecasts for all metrics."""
        all_forecasts = pd.DataFrame()

        for metric, (metric_column, agg_func) in self.metrics.items():
            # Handle grouping based on existing columns (no filter_column)
            group_data = self.filtered_video_df

            if group_data.empty:
                logging.info(f"Skipping empty dataset for metric: {metric}")
                continue

            # Handle risk_status
            # if metric == "risk_status_predicted":
            #     grouped_data, risk_mapping = self._transform_risk_status(group_data)
            # else:
            grouped_data = self._process_group_data(group_data, metric_column, agg_func)
            risk_mapping = None

            # Generate forecasts
            forecast = self._generate_forecasts(grouped_data, metric, risk_mapping)

            if not forecast.empty:
                all_forecasts = pd.concat([all_forecasts, forecast], ignore_index=True)

        # Filter forecasts by date range
        all_forecasts = all_forecasts[
            (all_forecasts["Date"] >= pd.to_datetime(self.start_date))
            & (all_forecasts["Date"] <= pd.to_datetime(self.end_date))
        ]

        # Pivot data to create one row per date with all metrics as columns
        pivoted_forecasts = all_forecasts.pivot_table(
            index="Date", columns="Metric", values="Predicted Value", aggfunc="first"
        ).reset_index()

        # Rename columns for the final output
        pivoted_forecasts.rename_axis(None, axis=1, inplace=True)

        # Convert Date to string for JSON output
        pivoted_forecasts["Date"] = pivoted_forecasts["Date"].dt.strftime("%Y-%m-%d")

        # Convert the result to a list of dictionaries
        return pivoted_forecasts.to_dict(orient="records")
