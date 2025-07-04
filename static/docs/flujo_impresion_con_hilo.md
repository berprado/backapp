# Flujo actualizado de impresión en hilo

La función `imprimir_en_hilo` ya no modifica directamente `st.session_state` desde el hilo de impresión. 
En su lugar, el hilo escribe los resultados en una **cola (`queue.Queue`)** y el hilo principal consume esos mensajes
para actualizar el estado de la interfaz.

1. `imprimir_en_hilo` crea la cola y retorna `(hilo_impresion, cola_resultados)`.
2. El hilo interno realiza la generación de PDF e impresión. Al completar o al detectar un error coloca
   en la cola un mensaje del tipo `("success", mensaje)` o `("error", mensaje)` y siempre agrega `("done", None)`
   al finalizar.
3. En la UI, `monitorear_hilo_impresion` recibe la cola y actualiza `st.session_state` según los mensajes
   recibidos, evitando modificaciones directas desde otros hilos.

Este mecanismo previene condiciones de carrera y mantiene la coherencia de `st.session_state`.
