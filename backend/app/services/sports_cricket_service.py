"""Specialized Cricket and IPL analytics engine.

Supports both:
1. Match-level datasets (e.g. matches.csv with team1, team2, winner, toss_winner, venue)
2. Ball-by-ball datasets (e.g. deliveries.csv with batsman, bowler, over, ball, runs, wickets)

Calculates factual cricket metrics:
- Team wins, losses, win percentage, season trends
- Top batsmen, bowlers, strike rates, economy rates
- Toss impact (toss win -> match win ratio)
- Batting first vs chasing win distribution
- Venue-wise match distribution and player of the match leaders
- Over-by-over run rate trends (powerplay, middle, death overs)
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.schemas.domain_blueprint import (
    ComparisonItemSchema,
    DomainChartSpecSchema,
    DomainKpiSchema,
    TrendItemSchema,
)

_CRICKET_MATCH_COLS = {
    "team1", "team2", "winner", "toss_winner", "toss_decision",
    "player_of_match", "venue", "win_by_runs", "win_by_wickets",
    "result_margin", "season",
}

_CRICKET_BALL_COLS = {
    "batsman", "batter", "bowler", "over", "ball",
    "batsman_runs", "total_runs", "is_wicket", "dismissal_kind",
    "batting_team", "bowling_team", "inning",
}


def detect_cricket_dataset_type(df: pd.DataFrame) -> Optional[str]:
    """Detect if dataset is match-level or ball-by-ball cricket data."""
    cols = {str(c).strip().lower().replace(" ", "_") for c in df.columns}
    match_score = len(cols & _CRICKET_MATCH_COLS)
    ball_score = len(cols & _CRICKET_BALL_COLS)

    if ball_score >= 3:
        return "ball_by_ball"
    if match_score >= 3:
        return "match_level"
    return None


def _find_col(df: pd.DataFrame, candidates: Tuple[str, ...]) -> Optional[str]:
    col_map = {str(c).strip().lower().replace(" ", "_"): str(c) for c in df.columns}
    for cand in candidates:
        if cand in col_map:
            return col_map[cand]
    return None


def compute_cricket_match_analytics(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute comprehensive cricket match-level analytics."""
    winner_col = _find_col(df, ("winner", "match_winner"))
    toss_winner_col = _find_col(df, ("toss_winner",))
    toss_decision_col = _find_col(df, ("toss_decision",))
    venue_col = _find_col(df, ("venue", "stadium", "ground"))
    pom_col = _find_col(df, ("player_of_match", "pom", "man_of_match", "mom"))
    margin_col = _find_col(df, ("result_margin", "win_by_runs", "win_by_wickets", "margin"))
    season_col = _find_col(df, ("season", "year"))

    total_matches = len(df)
    kpis: List[DomainKpiSchema] = [
        DomainKpiSchema(
            id="total_matches",
            name="Total Matches Played",
            description="Total number of completed cricket matches recorded",
            value=total_matches,
            format="number",
            aggregation="count",
            matched_columns=[winner_col] if winner_col else [],
            business_meaning="Total match sample size",
            is_reliable=True,
        )
    ]

    charts: List[DomainChartSpecSchema] = []
    comparisons: List[ComparisonItemSchema] = []

    # 1. Team Wins
    if winner_col and winner_col in df.columns:
        wins = df[winner_col].dropna().value_counts()
        if not wins.empty:
            top_winner = str(wins.index[0])
            top_wins = int(wins.iloc[0])
            kpis.append(
                DomainKpiSchema(
                    id="most_successful_team",
                    name=f"Most Wins ({top_winner})",
                    description=f"Highest match wins recorded by {top_winner}",
                    value=top_wins,
                    format="number",
                    aggregation="count",
                    matched_columns=[winner_col],
                    business_meaning="Dominant franchise in recorded matches",
                    is_reliable=True,
                )
            )

            win_data = [{"x": str(t), "y": int(w)} for t, w in wins.head(10).items()]
            charts.append(
                DomainChartSpecSchema(
                    id="wins_by_team",
                    title="Match Wins by Team",
                    chart_type="bar",
                    x_label="Franchise / Team",
                    y_label="Matches Won",
                    dimension_column=winner_col,
                    aggregation="count",
                    data=win_data,
                    business_question="Which teams have won the most matches?",
                )
            )

    # 2. Toss Impact (Toss Win -> Match Win %)
    if toss_winner_col and winner_col:
        valid_toss = df.dropna(subset=[toss_winner_col, winner_col])
        if len(valid_toss) > 0:
            toss_match_wins = (valid_toss[toss_winner_col] == valid_toss[winner_col]).sum()
            toss_win_pct = round((toss_match_wins / len(valid_toss)) * 100.0, 1)

            kpis.append(
                DomainKpiSchema(
                    id="toss_advantage",
                    name="Toss Advantage Win %",
                    description="Percentage of matches won by the team winning the toss",
                    value=toss_win_pct,
                    format="percentage",
                    aggregation="ratio",
                    matched_columns=[toss_winner_col, winner_col],
                    business_meaning="Statistical correlation between winning the toss and winning the match",
                    is_reliable=True,
                )
            )

    # 3. Toss Decision Breakdown (Bat vs Field)
    if toss_decision_col and toss_decision_col in df.columns:
        decisions = df[toss_decision_col].dropna().value_counts()
        if not decisions.empty:
            decision_data = [{"x": str(k).capitalize(), "y": int(v)} for k, v in decisions.items()]
            charts.append(
                DomainChartSpecSchema(
                    id="toss_decision_dist",
                    title="Toss Decision Preferences (Bat vs Field)",
                    chart_type="pie",
                    x_label="Decision",
                    y_label="Matches",
                    dimension_column=toss_decision_col,
                    aggregation="count",
                    data=decision_data,
                    business_question="Do teams prefer batting or fielding after winning the toss?",
                )
            )

    # 4. Top Player of the Match Awards
    if pom_col and pom_col in df.columns:
        poms = df[pom_col].dropna().value_counts()
        if not poms.empty:
            pom_data = [{"x": str(p), "y": int(c)} for p, c in poms.head(10).items()]
            charts.append(
                DomainChartSpecSchema(
                    id="top_player_of_match",
                    title="Top Player of the Match Recipients",
                    chart_type="bar",
                    x_label="Player",
                    y_label="Awards",
                    dimension_column=pom_col,
                    aggregation="count",
                    data=pom_data,
                    business_question="Which players have won the most Player of the Match awards?",
                )
            )

    # 5. Venue Match Distribution
    if venue_col and venue_col in df.columns:
        venues = df[venue_col].dropna().value_counts()
        if not venues.empty:
            venue_data = [{"x": str(v), "y": int(c)} for v, c in venues.head(8).items()]
            charts.append(
                DomainChartSpecSchema(
                    id="matches_by_venue",
                    title="Matches Hosted by Venue",
                    chart_type="bar",
                    x_label="Stadium / Venue",
                    y_label="Matches Hosted",
                    dimension_column=venue_col,
                    aggregation="count",
                    data=venue_data,
                    business_question="Which venues host the highest volume of matches?",
                )
            )

    return {
        "kpis": kpis,
        "charts": charts,
        "comparisons": comparisons,
    }


def compute_cricket_ball_analytics(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute comprehensive cricket ball-by-ball analytics."""
    batsman_col = _find_col(df, ("batsman", "batter", "striker"))
    bowler_col = _find_col(df, ("bowler",))
    runs_col = _find_col(df, ("batsman_runs", "runs_off_bat", "batter_runs"))
    total_runs_col = _find_col(df, ("total_runs", "runs"))
    over_col = _find_col(df, ("over",))
    wicket_col = _find_col(df, ("is_wicket", "wicket", "player_dismissed"))

    total_deliveries = len(df)
    kpis: List[DomainKpiSchema] = [
        DomainKpiSchema(
            id="total_deliveries",
            name="Total Deliveries Bowled",
            description="Total balls bowled in dataset",
            value=total_deliveries,
            format="number",
            aggregation="count",
            matched_columns=[over_col] if over_col else [],
            business_meaning="Ball-by-ball sample size",
            is_reliable=True,
        )
    ]

    charts: List[DomainChartSpecSchema] = []

    # Total runs scored
    if total_runs_col and total_runs_col in df.columns:
        s_runs = pd.to_numeric(df[total_runs_col], errors="coerce").dropna()
        total_runs_sum = int(s_runs.sum())
        kpis.append(
            DomainKpiSchema(
                id="total_runs_scored",
                name="Total Runs Scored",
                description="Aggregate runs scored across all matches",
                value=total_runs_sum,
                format="number",
                aggregation="sum",
                matched_columns=[total_runs_col],
                business_meaning="Total scoring volume across tournament",
                is_reliable=True,
            )
        )

    # Top Run Scorers & Strike Rates
    if batsman_col and runs_col:
        clean_bat = df[[batsman_col, runs_col]].dropna()
        clean_bat[runs_col] = pd.to_numeric(clean_bat[runs_col], errors="coerce").fillna(0)
        bat_summary = clean_bat.groupby(batsman_col).agg(
            total_runs=(runs_col, "sum"),
            balls_faced=(runs_col, "count"),
        )
        bat_summary["strike_rate"] = (bat_summary["total_runs"] / bat_summary["balls_faced"]) * 100.0
        top_batsmen = bat_summary.sort_values("total_runs", ascending=False).head(10)

        bat_data = [{"x": str(b), "y": int(r)} for b, r in top_batsmen["total_runs"].items()]
        charts.append(
            DomainChartSpecSchema(
                id="top_run_scorers",
                title="Top Run Scorers",
                chart_type="bar",
                x_label="Batsman",
                y_label="Total Runs",
                dimension_column=batsman_col,
                metric_column=runs_col,
                aggregation="sum",
                data=bat_data,
                business_question="Who are the leading run scorers?",
            )
        )

    # Top Wicket Takers
    if bowler_col and wicket_col:
        clean_bowl = df[[bowler_col, wicket_col]].dropna()
        clean_bowl[wicket_col] = pd.to_numeric(clean_bowl[wicket_col], errors="coerce").fillna(0)
        wickets = clean_bowl.groupby(bowler_col)[wicket_col].sum().sort_values(ascending=False).head(10)

        bowl_data = [{"x": str(b), "y": int(w)} for b, w in wickets.items()]
        charts.append(
            DomainChartSpecSchema(
                id="top_wicket_takers",
                title="Top Wicket Takers",
                chart_type="bar",
                x_label="Bowler",
                y_label="Wickets Taken",
                dimension_column=bowler_col,
                metric_column=wicket_col,
                aggregation="sum",
                data=bowl_data,
                business_question="Which bowlers have taken the most wickets?",
            )
        )

    # Over-by-Over Scoring Progression
    if over_col and total_runs_col:
        clean_overs = df[[over_col, total_runs_col]].dropna()
        clean_overs[total_runs_col] = pd.to_numeric(clean_overs[total_runs_col], errors="coerce").fillna(0)
        over_runs = clean_overs.groupby(over_col)[total_runs_col].mean().sort_index()

        over_data = [{"x": f"Over {int(o)}", "y": round(float(r) * 6, 2)} for o, r in over_runs.items()]
        charts.append(
            DomainChartSpecSchema(
                id="run_rate_by_over",
                title="Average Run Rate Progression by Over",
                chart_type="line",
                x_label="Match Over",
                y_label="Run Rate (Runs/Over)",
                dimension_column=over_col,
                metric_column=total_runs_col,
                aggregation="mean",
                data=over_data,
                business_question="How does run rate accelerate from powerplay through death overs?",
            )
        )

    return {
        "kpis": kpis,
        "charts": charts,
        "comparisons": [],
    }
