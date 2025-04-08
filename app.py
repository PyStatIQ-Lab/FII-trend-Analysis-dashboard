import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Load data function (in a real app, this would fetch from the API)
@st.cache_data
def load_data():
    # This would be replaced with actual API call in production
    # For now, we'll use the structure from the provided JSON
    data = {
        "year_month": "2025-April",
        "key_list": [
            "2024-October", "2024-November", "2024-December", 
            "2025-January", "2025-February", "2025-March", "2025-April"
        ],
        "data": {
            # Sample data structure from the JSON
            "2025-03-07": {
                "cash": {
                    "fii": {
                        "buy_sell_difference": -2035.1,
                        "buy": 8635.45,
                        "sell": 10670.55,
                        "net_action": "SELL",
                        "net_view": "BEARISH",
                        "net_view_strength": "Mild"
                    },
                    # ... rest of the data structure
                }
            }
        }
    }
    return data

def process_data(data):
    # Convert the nested data into a flat DataFrame for analysis
    records = []
    
    for date, daily_data in data['data'].items():
        record = {
            'date': date,
            'nifty': daily_data.get('nifty', None),
            'nifty_change_percent': daily_data.get('nifty_change_percent', None),
            'banknifty': daily_data.get('banknifty', None),
            'banknifty_change_percent': daily_data.get('banknifty_change_percent', None)
        }
        
        # Cash market data
        if 'cash' in daily_data:
            cash = daily_data['cash']
            if 'fii' in cash:
                fii_cash = cash['fii']
                record.update({
                    'fii_cash_buy': fii_cash.get('buy', None),
                    'fii_cash_sell': fii_cash.get('sell', None),
                    'fii_cash_net': fii_cash.get('buy_sell_difference', None),
                    'fii_cash_action': fii_cash.get('net_action', None),
                    'fii_cash_view': fii_cash.get('net_view', None),
                    'fii_cash_view_strength': fii_cash.get('net_view_strength', None)
                })
            
            if 'dii' in cash:
                dii_cash = cash['dii']
                record.update({
                    'dii_cash_buy': dii_cash.get('buy', None),
                    'dii_cash_sell': dii_cash.get('sell', None),
                    'dii_cash_net': dii_cash.get('buy_sell_difference', None),
                    'dii_cash_action': dii_cash.get('net_action', None),
                    'dii_cash_view': dii_cash.get('net_view', None),
                    'dii_cash_view_strength': dii_cash.get('net_view_strength', None)
                })
        
        # Futures data
        if 'future' in daily_data:
            future = daily_data['future']
            if 'fii' in future:
                fii_future = future['fii']
                if 'quantity-wise' in fii_future:
                    qty = fii_future['quantity-wise']
                    record.update({
                        'fii_future_net_oi': qty.get('net_oi', None),
                        'fii_future_action': qty.get('net_action', None),
                        'fii_future_view': qty.get('net_view', None),
                        'fii_future_view_strength': qty.get('net_view_strength', None)
                    })
                
                if 'amount-wise' in fii_future:
                    amt = fii_future['amount-wise']
                    record.update({
                        'fii_future_net_oi_amt': amt.get('net_oi', None),
                        'fii_future_view_amt': amt.get('net_view', None)
                    })
            
            if 'dii' in future:
                dii_future = future['dii']
                if 'quantity-wise' in dii_future:
                    qty = dii_future['quantity-wise']
                    record.update({
                        'dii_future_net_oi': qty.get('net_oi', None),
                        'dii_future_action': qty.get('net_action', None),
                        'dii_future_view': qty.get('net_view', None),
                        'dii_future_view_strength': qty.get('net_view_strength', None)
                    })
        
        # Options data
        if 'option' in daily_data:
            option = daily_data['option']
            if 'fii' in option:
                fii_option = option['fii']
                record.update({
                    'fii_option_overall_net_oi': fii_option.get('overall_net_oi', None),
                    'fii_option_action': fii_option.get('overall_net_oi_change_action', None),
                    'fii_option_view': fii_option.get('overall_net_oi_change_view', None),
                    'fii_option_view_strength': fii_option.get('overall_net_oi_change_view_strength', None)
                })
            
            if 'dii' in option:
                dii_option = option['dii']
                record.update({
                    'dii_option_overall_net_oi': dii_option.get('overall_net_oi', None),
                    'dii_option_action': dii_option.get('overall_net_oi_change_action', None),
                    'dii_option_view': dii_option.get('overall_net_oi_change_view', None),
                    'dii_option_view_strength': dii_option.get('overall_net_oi_change_view_strength', None)
                })
        
        records.append(record)
    
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    return df

def main():
    st.set_page_config(page_title="FII Analysis Dashboard", layout="wide")
    
    st.title("Foreign Institutional Investors (FII) Analysis Dashboard")
    st.markdown("Analyzing FII activities in Indian markets across cash, futures, and options segments")
    
    # Load and process data
    raw_data = load_data()
    df = process_data(raw_data)
    
    # Date range selector
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", min_date, min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("End date", max_date, min_value=min_date, max_value=max_date)
    
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    # Overview metrics
    st.subheader("Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        latest_fii_net = filtered_df['fii_cash_net'].iloc[-1]
        trend = "↑" if latest_fii_net > 0 else "↓"
        col1.metric("Latest FII Net (Cash)", f"{latest_fii_net:,.2f} Cr", trend)
    
    with col2:
        latest_dii_net = filtered_df['dii_cash_net'].iloc[-1]
        trend = "↑" if latest_dii_net > 0 else "↓"
        col2.metric("Latest DII Net (Cash)", f"{latest_dii_net:,.2f} Cr", trend)
    
    with col3:
        latest_nifty = filtered_df['nifty'].iloc[-1]
        nifty_change = filtered_df['nifty_change_percent'].iloc[-1]
        col3.metric("Nifty 50", f"{latest_nifty:,.2f}", f"{nifty_change:.2f}%")
    
    with col4:
        latest_banknifty = filtered_df['banknifty'].iloc[-1]
        banknifty_change = filtered_df['banknifty_change_percent'].iloc[-1]
        col4.metric("Bank Nifty", f"{latest_banknifty:,.2f}", f"{banknifty_change:.2f}%")
    
    # Cash Market Analysis
    st.subheader("Cash Market Activity")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=filtered_df['date'],
        y=filtered_df['fii_cash_buy'],
        name='FII Buy',
        marker_color='green'
    ))
    fig.add_trace(go.Bar(
        x=filtered_df['date'],
        y=filtered_df['fii_cash_sell'],
        name='FII Sell',
        marker_color='red'
    ))
    fig.add_trace(go.Scatter(
        x=filtered_df['date'],
        y=filtered_df['fii_cash_net'],
        name='FII Net',
        mode='lines+markers',
        line=dict(color='blue', width=2)
    ))
    
    fig.update_layout(
        barmode='group',
        title='FII Cash Market Activity (₹ Cr)',
        xaxis_title='Date',
        yaxis_title='Amount (₹ Cr)',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # FII vs DII Comparison
    st.subheader("FII vs DII Cash Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(filtered_df, x='date', y=['fii_cash_net', 'dii_cash_net'],
                     title='FII vs DII Net Investment (₹ Cr)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Create a summary table of actions
        latest_data = filtered_df.iloc[-1]
        summary_data = {
            'Metric': ['Cash Market', 'Futures (Qty)', 'Futures (Amt)', 'Options'],
            'FII Action': [
                latest_data['fii_cash_action'],
                latest_data['fii_future_action'],
                "N/A",  # No direct action field for amount-wise
                latest_data['fii_option_action']
            ],
            'FII View': [
                f"{latest_data['fii_cash_view']} ({latest_data['fii_cash_view_strength']})",
                f"{latest_data['fii_future_view']} ({latest_data['fii_future_view_strength']})",
                latest_data.get('fii_future_view_amt', 'N/A'),
                f"{latest_data['fii_option_view']} ({latest_data['fii_option_view_strength']})"
            ],
            'DII Action': [
                latest_data['dii_cash_action'],
                latest_data['dii_future_action'],
                "N/A",
                latest_data['dii_option_action']
            ],
            'DII View': [
                f"{latest_data['dii_cash_view']} ({latest_data['dii_cash_view_strength']})",
                f"{latest_data['dii_future_view']} ({latest_data['dii_future_view_strength']})",
                "N/A",
                f"{latest_data['dii_option_view']} ({latest_data['dii_option_view_strength']})"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, hide_index=True, use_container_width=True)
    
    # Derivatives Analysis
    st.subheader("Derivatives Activity")
    
    tab1, tab2, tab3 = st.tabs(["Futures (Quantity)", "Futures (Amount)", "Options"])
    
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=filtered_df['date'],
            y=filtered_df['fii_future_net_oi'],
            name='FII Net OI',
            marker_color='orange'
        ))
        fig.add_trace(go.Bar(
            x=filtered_df['date'],
            y=filtered_df['dii_future_net_oi'],
            name='DII Net OI',
            marker_color='purple'
        ))
        fig.update_layout(
            title='FII vs DII Futures Net OI (Quantity)',
            xaxis_title='Date',
            yaxis_title='Net Open Interest',
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        if 'fii_future_net_oi_amt' in filtered_df.columns:
            fig = px.line(filtered_df, x='date', y='fii_future_net_oi_amt',
                         title='FII Futures Net OI (Amount in ₹ Cr)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Amount-wise futures data not available in this dataset")
    
    with tab3:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=filtered_df['date'],
            y=filtered_df['fii_option_overall_net_oi'],
            name='FII Net OI',
            marker_color='teal'
        ))
        fig.add_trace(go.Bar(
            x=filtered_df['date'],
            y=filtered_df['dii_option_overall_net_oi'],
            name='DII Net OI',
            marker_color='pink'
        ))
        fig.update_layout(
            title='FII vs DII Options Net OI',
            xaxis_title='Date',
            yaxis_title='Net Open Interest',
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Market Correlation Analysis
    st.subheader("FII Activity vs Market Performance")
    
    fig = go.Figure()
    
    # Add FII net cash as bars
    fig.add_trace(go.Bar(
        x=filtered_df['date'],
        y=filtered_df['fii_cash_net'],
        name='FII Net (Cash)',
        marker_color='rgba(55, 128, 191, 0.7)',
        yaxis='y'
    ))
    
    # Add Nifty as a line on secondary y-axis
    fig.add_trace(go.Scatter(
        x=filtered_df['date'],
        y=filtered_df['nifty'],
        name='Nifty 50',
        line=dict(color='red', width=2),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='FII Net Investment vs Nifty 50',
        xaxis_title='Date',
        yaxis=dict(
            title='FII Net Investment (₹ Cr)',
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue')
        ),
        yaxis2=dict(
            title='Nifty 50',
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Raw data view
    st.subheader("Raw Data")
    st.dataframe(filtered_df, use_container_width=True)

if __name__ == "__main__":
    main()
