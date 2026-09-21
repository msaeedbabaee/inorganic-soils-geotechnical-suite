import io
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import interp1d
import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Inorganic Soils Geotechnical Suite", page_icon="🧪", layout="wide"
)

# --- OOP COMPUTATIONAL ENGINES ---


class GrainSizeAnalyzer:
    """Engine for grain size distribution curve analysis (ASTM D6913 & D7928)."""

    def __init__(self, df_sieve: pd.DataFrame):
        # df_sieve must have columns: ['grain_size_mm', 'percent_passing']
        self.df = df_sieve.sort_values(by="grain_size_mm", ascending=False).reset_index(
            drop=True
        )

    def calculate_coefficients(self):
        sizes = self.df["grain_size_mm"].values
        passing = self.df["percent_passing"].values

        # Filter out zero or negative passing for log interpolation
        valid = (sizes > 0) & (passing > 0) & (passing < 100)
        if sum(valid) < 2:
            return None, None, None, 0.0, 0.0, "Insufficient data points for curve fit."

        log_sizes = np.log10(sizes[valid])
        pass_vals = passing[valid]

        try:
            # Interpolation function for log(size) vs percent passing
            f_interp = interp1d(
                pass_vals, log_sizes, kind="linear", fill_value="extrapolate"
            )

            # Find D10, D30, D60
            d10 = 10 ** float(f_interp(10.0))
            d30 = 10 ** float(f_interp(30.0))
            d60 = 10 ** float(f_interp(60.0))

            cu = d60 / d10 if d10 > 0 else 0.0
            cc = (d30**2) / (d10 * d60) if (d10 * d60) > 0 else 0.0

            # Grading evaluation (Unified Soil Classification System criteria)
            # Assuming coarse-grained boundary checks typically handled externally, but general definition:
            grading = "Borderline / Unclassified"
            # Basic check for gravel/sand general well-graded criteria
            return d10, d30, d60, cu, cc, "Success"
        except Exception as e:
            return None, None, None, 0.0, 0.0, str(e)


class VisualSoilDescriptionEngine:
    """Engine for visual-manual soil identification and description (ASTM D2488)."""

    def __init__(
        self,
        soil_name,
        color,
        moisture,
        plasticity,
        dry_strength,
        dilatancy,
        toughness,
        angularity,
        particle_shape,
        hcl_reaction,
    ):
        self.soil_name = soil_name
        self.color = color
        self.moisture = moisture
        self.plasticity = plasticity
        self.dry_strength = dry_strength
        self.dilatancy = dilatancy
        self.toughness = toughness
        self.angularity = angularity
        self.particle_shape = particle_shape
        self.hcl_reaction = hcl_reaction

    def generate_description_string(self) -> str:
        desc = f"{self.color}, {self.moisture} {self.soil_name}; "
        if self.soil_name in ["Lean Clay", "Fat Clay", "Elastic Silt", "Silt"]:
            desc += f"Plasticity: {self.plasticity}, Dry Strength: {self.dry_strength}, "
            desc += f"Dilatancy: {self.dilatancy}, Toughness: {self.toughness}."
        else:
            desc += f"Particle Angularity: {self.angularity}, Shape: {self.particle_shape}."

        if self.hcl_reaction != "None":
            desc += f" Reaction with HCl: {self.hcl_reaction}."
        return desc


class RelativeDensityCalculator:
    """Engine for relative density (Dr) and compactness calculations."""

    def __init__(
        self,
        method="Void Ratio",
        e=None,
        e_min=None,
        e_max=None,
        gamma_d=None,
        gamma_d_min=None,
        gamma_d_max=None,
    ):
        self.method = method
        self.e = e
        self.e_min = e_min
        self.e_max = e_max
        self.gamma_d = gamma_d
        self.gamma_d_min = gamma_d_min
        self.gamma_d_max = gamma_d_max

    def compute(self):
        if self.method == "Void Ratio":
            if (
                self.e_max is None
                or self.e_min is None
                or self.e is None
                or self.e_max == self.e_min
            ):
                return 0.0, "Invalid Input"
            dr = (
                (self.e_max - self.e) / (self.e_max - self.e_min)
            ) * 100.0
        else:
            if (
                self.gamma_d_min is None
                or self.gamma_d_max is None
                or self.gamma_d is None
                or self.gamma_d_max == self.gamma_d_min
            ):
                return 0.0, "Invalid Input"
            dr = (
                (self.gamma_d_max * (self.gamma_d - self.gamma_d_min))
                / (self.gamma_d * (self.gamma_d_max - self.gamma_d_min))
            ) * 100.0

        dr = float(np.clip(dr, 0.0, 100.0))

        # Compactness classification (CFEM Table 4.3 equivalent)
        if dr < 15:
            compactness = "Very Loose"
        elif dr < 35:
            compactness = "Loose"
        elif dr < 65:
            compactness = "Medium Dense"
        elif dr < 85:
            compactness = "Dense"
        else:
            compactness = "Very Dense"

        return dr, compactness


# --- STREAMLIT USER INTERFACE ---

st.title("🧪 Inorganic Soils Geotechnical Suite (CFEM Chapter 4)")
st.markdown(
    "Production-grade analysis platform covering **Grain Size Curves**, **Visual-Manual Classification (ASTM D2488)**, and **Relative Density Computations**."
)

tab1, tab2, tab3 = st.tabs(
    [
        "📈 Grain Size & Gradation",
        "📝 Visual-Manual Description",
        "⚖️ Relative Density & Compactness",
    ]
)

# --- TAB 1: GRAIN SIZE ANALYSIS ---
with tab1:
    st.header("Grain Size Distribution & Gradation Curve Analyzer")
    st.write(
        "Analyze sieve and hydrometer test data to extract \(D_{10}, D_{30}, D_{60}\) and grading coefficients."
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Input Sieve Data")
        default_data = pd.DataFrame(
            {
                "grain_size_mm": [
                    50.0,
                    25.0,
                    9.5,
                    4.75,
                    2.0,
                    0.85,
                    0.425,
                    0.150,
                    0.075,
                ],
                "percent_passing": [
                    100.0,
                    90.0,
                    75.0,
                    60.0,
                    45.0,
                    32.0,
                    22.0,
                    10.0,
                    5.0,
                ],
            }
        )

        edited_sieve_df = st.data_editor(
            default_data, num_rows="dynamic", use_container_width=True
        )

    with col2:
        st.subheader("Gradation Curve & Results")
        if not edited_sieve_df.empty:
            analyzer = GrainSizeAnalyzer(edited_sieve_df)
            d10, d30, d60, cu, cc, status = analyzer.calculate_coefficients()

            if status == "Success":
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("D10 (mm)", f"{d10:.3f}")
                m2.metric("D30 (mm)", f"{d30:.3f}")
                m3.metric("D60 (mm)", f"{d60:.3f}")
                m4.metric("Cu", f"{cu:.2f}")
                m5.metric("Cc", f"{cc:.2f}")

                # Plotly Interactive Chart
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=edited_sieve_df["grain_size_mm"],
                        y=edited_sieve_df["percent_passing"],
                        mode="lines+markers",
                        name="Gradation Curve",
                        line=dict(color="blue", width=2),
                    )
                )
                fig.update_xaxes(
                    type="log",
                    autorange="reversed",
                    title="Grain Size (mm) [Log Scale]",
                )
                fig.update_yaxes(
                    title="Percent Passing (%)", range=[0, 100]
                )
                fig.update_layout(
                    title="Particle Size Distribution Curve",
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=350,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(
                    "Please provide valid, strictly descending sieve sizes with passing percentages between 0 and 100."
                )

# --- TAB 2: VISUAL-MANUAL DESCRIPTION ---
with tab2:
    st.header("Visual-Manual Soil Description Generator (ASTM D2488)")
    st.write(
        "Generate professional field identification descriptions based on qualitative index properties."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        soil_name = st.selectbox(
            "Primary Soil Type",
            [
                "Lean Clay",
                "Fat Clay",
                "Silt",
                "Elastic Silt",
                "Sand",
                "Gravel",
                "Sandy Lean Clay",
            ],
        )
        color = st.selectbox(
            "Color",
            [
                "Brown",
                "Dark Brown",
                "Gray",
                "Dark Gray",
                "Reddish Brown",
                "Yellowish Brown",
            ],
        )
        moisture = st.selectbox("Moisture Condition", ["Dry", "Moist", "Wet"])
    with c2:
        plasticity = st.selectbox(
            "Plasticity (Fine Soils)", ["Non-plastic", "Low", "Medium", "High"]
        )
        dry_strength = st.selectbox(
            "Dry Strength", ["None", "Low", "Medium", "High", "Very High"]
        )
        dilatancy = st.selectbox(
            "Dilatancy (Reaction to Shaking)", ["None", "Slow", "Rapid"]
        )
    with c3:
        toughness = st.selectbox(
            "Toughness (Consistency near PL)", ["Low", "Medium", "High"]
        )
        angularity = st.selectbox(
            "Angularity (Coarse Soils)",
            ["Angular", "Sub-angular", "Sub-rounded", "Rounded"],
        )
        particle_shape = st.selectbox(
            "Particle Shape", ["Flat", "Elongated", "Flat and Elongated", "None"]
        )
        hcl_reaction = st.selectbox("Reaction with HCl", ["None", "Weak", "Strong"])

    desc_engine = VisualSoilDescriptionEngine(
        soil_name,
        color,
        moisture,
        plasticity,
        dry_strength,
        dilatancy,
        toughness,
        angularity,
        particle_shape,
        hcl_reaction,
    )
    final_desc = desc_engine.generate_description_string()

    st.success(f"**Standard Descriptive Name:** \n\n `{final_desc}`")

# --- TAB 3: RELATIVE DENSITY ---
with tab3:
    st.header("Relative Density & Compactness Calculator")
    st.write(
        "Compute relative density (\(D_d\)) for coarse-grained soils according to CFEM equations."
    )

    method = st.radio(
        "Calculation Method:", ("Void Ratio (\(e, e_{max}, e_{min}\))", "Dry Unit Weight (\(\gamma_d, \gamma_{min}, \gamma_{max}\))")
    )

    if method.startswith("Void"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            e = st.number_input("In-situ Void Ratio (\(e\))", value=0.65, step=0.01)
        with col_b:
            e_min = st.number_input(
                "Minimum Void Ratio (\(e_{min}\))", value=0.45, step=0.01
            )
        with col_c:
            e_max = st.number_input(
                "Maximum Void Ratio (\(e_{max}\))", value=0.85, step=0.01
            )
        rd_calc = RelativeDensityCalculator(
            method="Void Ratio", e=e, e_min=e_min, e_max=e_max
        )
    else:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            gamma_d = st.number_input(
                "Dry Unit Weight \(\\gamma_d\) (\(kN/m^3\))", value=16.5, step=0.1
            )
        with col_b:
            gamma_d_min = st.number_input(
                "Min Dry Unit Weight \(\\gamma_{min}\) (\(kN/m^3\))",
                value=14.0,
                step=0.1,
            )
        with col_c:
            gamma_d_max = st.number_input(
                "Max Dry Unit Weight \(\\gamma_{max}\) (\(kN/m^3\))",
                value=18.5,
                step=0.1,
            )
        rd_calc = RelativeDensityCalculator(
            method="Unit Weight",
            gamma_d=gamma_d,
            gamma_d_min=gamma_d_min,
            gamma_d_max=gamma_d_max,
        )

    if st.button("Compute Relative Density", type="primary"):
        dr_val, compactness = rd_calc.compute()
        st.metric("Relative Density (\(D_d\))", f"{dr_val:.1f} %")
        st.info(f"**Compactness State:** `{compactness}`")

# --- EXPORT REPORT UTILITY ---
st.markdown("---")
if st.button("📥 Export Comprehensive Report (.xlsx)"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inorganic Soils Summary"
    ws["A1"] = "Inorganic Soils Geotechnical Analysis Summary"
    ws["A3"] = "Module"
    ws["B3"] = "Result / Status"
    ws["A4"] = "Visual Description"
    ws["B4"] = final_desc
    ws["A5"] = "Relative Density"
    ws["B5"] = f"{dr_val:.1f}% ({compactness})"

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    st.download_button(
        label="Download Formatted Excel Report",
        data=output,
        file_name="Inorganic_Soils_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
