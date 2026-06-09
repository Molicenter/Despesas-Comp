# Botão mestre para processar todas as avaliações feitas na tabela
            if st.button("💾 Salvar Alterações no Sistema", type="primary"):
                mudancas = edited_df[edited_df['Avaliação 📝'] != 'Pendente']
                
                if mudancas.empty:
                    st.warning("⚠️ Nenhuma avaliação foi alterada. Mude o status para 'Aprovado' ou 'Reprovado' na tabela antes de salvar.")
                else:
                    with st.spinner(f"⏳ Processando e salvando {len(mudancas)} avaliações de uma vez..."):
                        
                        # Cria uma lista/pacote com todas as alterações para enviar de uma vez só
                        lista_atualizacoes = []
                        for idx, row in mudancas.iterrows():
                            lista_atualizacoes.append({
                                "Loja": row['Loja'],
                                "Nome": row['Nome Completo'],
                                "Valor": float(row['Valor']),
                                "NovoStatus": row['Avaliação 📝']
                            })
                            
                        payload = {
                            "action": "bulk_update",
                            "updates": lista_atualizacoes
                        }
                        
                        sucesso_geral = False
                        try:
                            # Faz um único envio rápido
                            requests.post(URL_API_DESPESAS, json=payload, timeout=20)
                            sucesso_geral = True
                        except Exception as e:
                            st.error(f"Erro de conexão ao salvar: {e}")
                        
                        # Limpa e recarrega após salvar
                        if sucesso_geral:
                            st.success("✅ Avaliações salvas com sucesso!")
                            st.cache_data.clear()
                            time.sleep(1.5)
                            st.rerun()

        st.markdown("<br><hr>", unsafe_allow_html=True)
        with st.expander("📚 Ver Histórico Geral de Avaliações", expanded=False):
            if df_historico.empty:
                st.info("Nenhuma despesa foi avaliada ainda.")
            else:
                df_historico = df_historico.iloc[::-1].reset_index(drop=True)
                st.dataframe(df_historico, use_container_width=True, hide_index=True)
