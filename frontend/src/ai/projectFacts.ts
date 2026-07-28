import { estimates, projects, threads } from '../data/mock'
import type { ProjectFact } from './service'
import type { AuditEntry } from './context'

const rub = (value: number) => `${value.toLocaleString('ru-RU')} руб`

/**
 * Факты о проекте для ассистента.
 *
 * Все числа считаются здесь, в коде продукта. Модель их только переписывает:
 * бэкенд отклонит ответ, где появилась сумма, отсутствующая в источниках.
 * Поэтому ассистент не может ошибиться в арифметике — он её не делает.
 */
export function buildProjectFacts(audit: AuditEntry[]): ProjectFact[] {
  const facts: string[] = []
  const project = projects[0]

  if (project) {
    const left = project.budget - project.spent
    facts.push(
      `Проект «${project.name}», адрес ${project.address}, площадь ${project.area} м², ` +
        `${project.rooms} комнаты, статус: в работе.`,
    )
    facts.push(
      `Бюджет проекта ${rub(project.budget)}, потрачено ${rub(project.spent)}, ` +
        `остаток ${rub(left)}, прогресс ${project.progress}%.`,
    )
    facts.push(
      `Сроки проекта: с ${project.startDate} по ${project.endDate}.`,
    )

    for (const stage of project.stages) {
      facts.push(
        `Этап «${stage.name}»: статус ${stage.status}, готовность ${stage.progress}%, ` +
          `бюджет ${rub(stage.budget)}, потрачено ${rub(stage.spent)}, ` +
          `ответственный ${stage.responsible}, срок до ${stage.endDate}.`,
      )
    }

    for (const member of project.team) {
      facts.push(`В команде: ${member.name}, роль ${member.role}.`)
    }
  }

  const estimate = estimates[0]
  if (estimate) {
    facts.push(
      `Смета от подрядчика ${estimate.contractor} на сумму ${rub(estimate.total)}, ` +
        `${estimate.items.length} позиций.`,
    )
    for (const item of estimate.items) {
      facts.push(
        `Позиция сметы «${item.name}»: ${item.quantity} ${item.unit} по ` +
          `${rub(item.price)} за единицу, итого ${rub(item.total)}.`,
      )
    }
  }

  for (const thread of threads) {
    const last = thread.messages[thread.messages.length - 1]
    if (!last) continue
    facts.push(
      `Переписка «${thread.title}» (${thread.zone}, ${thread.stage}), ` +
        `статус ${thread.status}. Последнее сообщение от ${last.author}: «${last.text}»`,
    )
  }

  // Подтверждения человека — это состояние проекта, а не журнал интерфейса:
  // ассистент обязан их видеть, иначе будет отвечать про устаревший бюджет.
  for (const entry of audit) {
    facts.push(`${entry.action} в ${entry.ts}: ${entry.detail}.`)
  }

  if (audit.length === 0) {
    facts.push('Пока ни одно предложение AI-координатора не подтверждено человеком.')
  }

  return facts.map((text, index) => ({ id: index + 1, text }))
}
