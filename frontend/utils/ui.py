import streamlit as st

def apply_custom_theme():
    """Applies global CSS styling rules for the custom Forest Green palette

    and smooth scroll animations across all Streamlit views.
    """
    st.markdown("""
    <style>
        /* Import Outfit & Inter fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Inter:wght@400;500;700&display=swap');
        
        /* Hide default Streamlit header, main menu, and footer branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        div[data-testid="stHeader"] {display: none;}
        
        /* Smooth Scrolling */
        html {
            scroll-behavior: smooth !important;
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #142718;
        }
        ::-webkit-scrollbar-thumb {
            background: #2E5B41;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #98CBB0;
        }
        
        /* Font Family styling */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', sans-serif !important;
            color: #E7EFE4 !important;
            font-weight: 700 !important;
        }
        
        div, span, p, label {
            font-family: 'Inter', sans-serif !important;
        }

        /* Metric styling */
        div[data-testid="stMetricValue"] {
            color: #98CBB0 !important;
            font-weight: 800 !important;
            font-size: 2.2rem !important;
            font-family: 'Outfit', sans-serif !important;
        }
        
        div[data-testid="stMetricLabel"] {
            color: #E7EFE4 !important;
            font-weight: 500 !important;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            font-size: 0.85rem !important;
        }
        
        /* Page element scroll entrance transition */
        [data-testid="stVerticalBlock"] > div {
            animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(24px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Tabs styling */
        button[data-baseweb="tab"] {
            color: #98CBB0 !important;
            font-weight: 600 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #E7EFE4 !important;
            border-bottom-color: #98CBB0 !important;
        }

        /* DataFrame & Tables header customization */
        .stDataFrame th {
            background-color: #2E5B41 !important;
            color: #E7EFE4 !important;
        }
    </style>
    """, unsafe_allow_html=True)


def style_plotly_fig(fig):
    """Formats plotly diagrams to seamlessly blend into the Forest Green UI."""
    fig.update_layout(
        plot_bgcolor="rgba(20, 39, 24, 1)",
        paper_bgcolor="rgba(20, 39, 24, 0)",
        font_color="#E7EFE4",
        font_family="Inter, sans-serif",
        title_font_family="Outfit, sans-serif"
    )
    
    # Polar Chart adjustments
    if hasattr(fig, 'data') and len(fig.data) > 0 and fig.data[0].type == 'scatterpolar':
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    color="#98CBB0",
                    gridcolor="rgba(152, 203, 176, 0.15)",
                ),
                angularaxis=dict(
                    gridcolor="rgba(152, 203, 176, 0.15)",
                    linecolor="#98CBB0",
                ),
                bgcolor="rgba(20, 39, 24, 1)"
            )
        )
    else:
        # Standard axes updates
        fig.update_xaxes(
            gridcolor="rgba(152, 203, 176, 0.1)",
            linecolor="rgba(152, 203, 176, 0.2)",
            zerolinecolor="rgba(152, 203, 176, 0.2)"
        )
        fig.update_yaxes(
            gridcolor="rgba(152, 203, 176, 0.1)",
            linecolor="rgba(152, 203, 176, 0.2)",
            zerolinecolor="rgba(152, 203, 176, 0.2)"
        )
        
    return fig
