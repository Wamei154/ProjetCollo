def main():
    st.sidebar.header("Sélection")

    # Définir la date de début de la première semaine
    start_date = datetime.strptime("16/09/2024", "%d/%m/%Y")
    current_date = datetime.now()

    # Calculer les semaines actuelle et suivante
    current_week_start, next_week_start = get_week_dates(start_date, current_date)

    # Formatage des dates au style JJ/MM
    current_week_str = current_week_start.strftime("%d/%m")
    next_week_str = next_week_start.strftime("%d/%m")

    # Afficher les dates des semaines dans la barre latérale
    st.sidebar.write(f"**Semaine actuelle** : {current_week_str}")
    st.sidebar.write(f"**Semaine suivante** : {next_week_str}")

    classe = st.sidebar.selectbox("TSI", options=["1", "2"], index=0)
    groupe = st.sidebar.text_input("Groupe", value="G1")
    semaine = st.sidebar.text_input("Semaine", value="1")

    if st.sidebar.button("Afficher"):
        st.session_state.groupe = groupe
        st.session_state.semaine = semaine
        st.session_state.classe = classe
        display_data()

    st.markdown(
        """
        <div style="position: fixed; bottom: 0; width: 100%; font-size: 10px;">
            Fait par BERRY Mael, avec l'aide de SOUVELAIN Gauthier et de DAMBRY Paul
        </div>
        """,
        unsafe_allow_html=True,
    )
