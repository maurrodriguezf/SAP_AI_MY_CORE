from gen_ai_hub.orchestration.models.message import SystemMessage, UserMessage
from gen_ai_hub.orchestration.models.template import Template
from gen_ai_hub.orchestration.models.config import OrchestrationConfig
from gen_ai_hub.orchestration.models.llm import LLM
from gen_ai_hub.orchestration.models.template import TemplateValue
from gen_ai_hub.orchestration.service import OrchestrationService
from gen_ai_hub.orchestration.models.message import ToolMessage

# Definimos el prompt (puede almacenarse en el Prompt Registry)
template = Template(
    messages=[
        SystemMessage(
          "Eres un asistente de mantenimiento SAP. "
          "Completa la notificación de orden utilizando la función disponible."
        ),
        UserMessage(
          "Por favor actualiza la notificación {{?notif_id}} "
          "con puesto de trabajo {{?puesto_trabajo}}, clase {{?clase_act}}, "
          "trabajo real {{?trabajo_real}} h, inicio {{?inicio}}, fin {{?fin}}, "
          "fecha contable {{?fecha_contab}}."
        )
    ],
    tools=[actualizar_notificacion]  # Lista de herramientas
)

# Seleccionamos un modelo compatible (por ejemplo, gpt-4o-mini)
llm = LLM(name="gpt-4o-mini", version="latest",
          parameters={"max_tokens": 500, "temperature": 0.0})

config = OrchestrationConfig(template=template, llm=llm)

# Valores concretos que se enviarán al prompt
template_values = [
    TemplateValue(name="notif_id", value="1944156"),
    TemplateValue(name="puesto_trabajo", value="Q0CC"),
    TemplateValue(name="clase_act", value="002"),
    TemplateValue(name="trabajo_real", value=5.0),
    TemplateValue(name="inicio", value="202507150700"),
    TemplateValue(name="fin", value="202507151626"),
    TemplateValue(name="fecha_contab", value="20250715")
]

service = OrchestrationService()

# Primera ejecución: el modelo puede decidir invocar la función
response = service.run(config=config, template_values=template_values)
tool_calls = response.orchestration_result.choices[0].message.tool_calls

# Ejecutamos la herramienta con los argumentos propuestos por el modelo
history = []
history.extend(response.module_results.templating)
history.append(response.orchestration_result.choices[0].message)

for call in tool_calls:
    # Ejecutamos la función y añadimos la respuesta al historial
    result = actualizar_notificacion.execute(**call.function.parse_arguments())
    tool_message = ToolMessage(content=str(result), tool_call_id=call.id)
    history.append(tool_message)

# Segunda ejecución: el modelo recibe el resultado y genera la respuesta final
response2 = service.run(config=config,
                        template_values=template_values,
                        history=history)
print(response2.orchestration_result.choices[0].message.content)