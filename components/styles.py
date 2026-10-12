import streamlit as st

def apply_custom_styles():
    st.markdown("""
        <style>
        .main .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2.5rem;
            max-width: 1200px;
        }
        
        .metric-card {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            margin-bottom: 15px;
            transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
        }
        
        .metric-title {
            color: #6b7280;
            font-size: 0.82rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }
        .metric-value {
            color: #111827;
            font-size: 1.65rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .metric-sub {
            color: #4b5563;
            font-size: 0.8rem;
            margin-top: 4px;
        }

        .badge-income {
            background-color: #ecfdf5;
            color: #047857;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-expense {
            background-color: #fef2f2;
            color: #b91c1c;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .insight-card {
            background-color: #f9fafb;
            border-left: 4px solid #3b82f6;
            padding: 14px 18px;
            border-radius: 6px;
            margin-bottom: 12px;
        }
        .insight-card.danger {
            border-left-color: #ef4444;
            background-color: #fef2f2;
        }
        .insight-card.warning {
            border-left-color: #f59e0b;
            background-color: #fffbeb;
        }
        .insight-card.info {
            border-left-color: #3b82f6;
            background-color: #eff6ff;
        }
        .insight-title {
            font-weight: 600;
            font-size: 0.95rem;
            color: #1f2937;
            margin-bottom: 4px;
        }
        .insight-body {
            font-size: 0.88rem;
            color: #4b5563;
            line-height: 1.4;
        }
        </style>
    """, unsafe_allow_html=True)

def format_currency(amount: float, currency_code: str = "INR") -> str:
    curr_symbols = {
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
    }
    symbol = curr_symbols.get(currency_code, "₹")
    
    if currency_code == "INR":
        abs_amt = abs(amount)
        parts = f"{abs_amt:.2f}".split(".")
        integer_part = parts[0]
        decimal_part = parts[1]

        if len(integer_part) > 3:
            last3 = integer_part[-3:]
            remaining = integer_part[:-3]
            pairs = []
            while len(remaining) > 2:
                pairs.insert(0, remaining[-2:])
                remaining = remaining[:-2]
            if remaining:
                pairs.insert(0, remaining)
            formatted_int = ",".join(pairs) + "," + last3
        else:
            formatted_int = integer_part

        formatted = f"{formatted_int}.{decimal_part}"
        return f"{'-' if amount < 0 else ''}{symbol}{formatted}"
    else:
        return f"{'-' if amount < 0 else ''}{symbol}{abs(amount):,.2f}"
