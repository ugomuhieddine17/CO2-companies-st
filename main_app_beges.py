#############################
####       PACKAGES      ####
#############################

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import altair as alt
from altair import expr, datum
import base64
import itertools 


st.set_page_config(layout = 'wide')
@st.cache_data
def full_initialisation(saved=True, DATA_PATH='./data'):
    #data reading

    if saved:
        df_assess = pd.read_pickle(f'{DATA_PATH}/assess.pkl')
        df_emissions = pd.read_pickle(f'{DATA_PATH}/emissions.pkl')
        df_postes = pd.read_pickle(f'{DATA_PATH}/postes.pkl')
        df_scopes = pd.read_pickle(f'{DATA_PATH}/scopes.pkl')
        df_descriptions = pd.read_pickle(f'{DATA_PATH}/descriptions.pkl')
        df_emission_bilan = pd.read_pickle(f'{DATA_PATH}/emission_bilan.pkl')
        df_reduction_bilan = pd.read_pickle(f'{DATA_PATH}/reduction_bilan.pkl')

    else:
        file_name =  DATA_PATH + '/bilans-ges.xls'
        
        df_assess = pd.read_excel(io=file_name, sheet_name="assessments")
        df_emissions = pd.read_excel(io=file_name, sheet_name="Détail émissions")
        df_postes = pd.read_excel(io=file_name, sheet_name="Postes")
        df_scopes = pd.read_excel(io=file_name, sheet_name="Scopes")
        df_descriptions = pd.read_excel(io=file_name, sheet_name="Descriptions")
        df_emission_bilan = pd.read_excel(io=file_name, sheet_name="assessment_bilan")
        df_reduction_bilan = pd.read_excel(io=file_name, sheet_name="assessment_reduction")
    
    #PROCESS
    # dico scope et poste
    dico_postes = {x.id:x.label for (idx, x) in df_postes.iterrows()}
    dico_scopes = {x.Scope:x.Description for (idx, x) in df_scopes.iterrows()}
    dico_postes_to_scopes = {x.id:x.scope_id for (idx, x) in df_postes.iterrows()}

    # process generally the data
    #DF EMISSIONS
    df_emissions = df_emissions.rename(columns={'scope_item_id':'poste_item_id'})
    df_emissions[['total', 'co2_biogenic']] = df_emissions[['total', 'co2_biogenic']].fillna(0)
    df_emissions['poste_item'] = df_emissions.poste_item_id.map(dico_postes)
    df_emissions['scope_item'] = df_emissions.poste_item_id.map(dico_postes_to_scopes)

    #DF REDUCTION BILAN

    df_reduction_bilan[['reductions_scope_1_2', 'reductions_scope_1', 'reductions_scope_2',
        'reductions_scope_3']] = df_reduction_bilan[['reductions_scope_1_2', 'reductions_scope_1', 'reductions_scope_2',
        'reductions_scope_3']].fillna(0)
    
    return dico_postes, dico_postes_to_scopes, df_assess, df_emissions, df_postes, df_scopes, df_descriptions, df_emission_bilan, df_reduction_bilan

dico_postes, dico_postes_to_scopes, df_assess, df_emissions, df_postes, df_scopes, df_descriptions, df_emission_bilan, df_reduction_bilan = full_initialisation()


#######################################
####           MAIN PAGE           ####
#######################################


# Set header title
st.title('Comprendre les BEGES des organisations françaises')

selected_organization_name = st.selectbox(
    'Qui observer ?',
    list(df_assess.organization_name.unique())
    )


#GENERAL INFO 
loc_info = df_assess[df_assess.organization_name == selected_organization_name]
loc_assess_id = loc_info.id.values[0]
loc_reporting_year = df_emission_bilan[df_emission_bilan.assessment_id == loc_assess_id].reporting_year.values[0]

#EMISSION
loc_emission = df_emissions[df_emissions.assessment_id == loc_assess_id]

loc_chart_poste_emission = alt.Chart(loc_emission).mark_bar().encode(
        x='poste_item_id',
        y='total:Q',
        color='scope_item:N',
        tooltip=[
            alt.Tooltip('poste_item', title='scope_item'),
        ]
        ).properties(
                width=500,
                height=300
                )
loc_total_emissions = loc_emission.total.sum()


#REDUCTION
loc_reduc_bilan = df_reduction_bilan[df_reduction_bilan.id == loc_assess_id].copy()
loc_has_plan = loc_reduc_bilan.action_plan.values[0] == 'Oui'


loc_reduc_bilan = loc_reduc_bilan[['id', 'reductions_scope_1_2', 'reductions_scope_1', 'reductions_scope_2',
       'reductions_scope_3']].melt(id_vars='id')

loc_reduced_emission = loc_reduc_bilan.value.sum()

loc_chart_reduced_emission = alt.Chart(loc_reduc_bilan).mark_bar().encode(
        x=alt.X('variable:N'),
        y='value:Q',
        ).properties(
                width=500,
                height=300
                )

## MARKDOWN PLOT
st.markdown(f"## :blue[Informations générales]")
st.markdown(f"{loc_info.organization_description.values[0]}")
st.markdown(f"#### Taille \n {loc_info.staff.values[0]:.0f} collaborators")
st.markdown(f"#### Année de reporting \n {loc_reporting_year}")
st.divider() 
st.markdown(f"## :blue[Description BEGES]")
if loc_has_plan:
    st.markdown('### :green[L\'organisation possède un plan de transition]')
else:
    st.markdown('### :red[L\'organisation ne possède PAS un plan de transition]')

if (loc_reduced_emission/loc_total_emissions) < 0.1:
    st.markdown(f"#### Ratio d'émissions réduites \n **:red[{(loc_reduced_emission/loc_total_emissions)*100:.2f} %]**")

else:
    st.markdown(f"#### Ratio d'émissions réduites \n **:green[{(loc_reduced_emission/loc_total_emissions)*100:.2f} %]**")

st.markdown(f" _Source du rapport {loc_info.source_url.values[0]}_ ")

st.altair_chart(loc_chart_poste_emission, use_container_width=True)
st.divider() 


#DESCRIPTION
loc_description  = df_descriptions[df_descriptions.assessment_id == loc_assess_id].copy()
loc_description_potentiel = loc_description.key.tolist()

st.markdown(f'''## :blue[Méthodologie]''')

selected_descrip = st.selectbox(
    'Quelle méthodologie observer ?',
    loc_description_potentiel
    )
loc_descrip_to_print = loc_description[loc_description.key == selected_descrip].value.values[0]

st.markdown(f'''#### {selected_descrip} \n {loc_descrip_to_print}''')


## Altair PLOTS

st.altair_chart(loc_chart_reduced_emission, use_container_width=True)