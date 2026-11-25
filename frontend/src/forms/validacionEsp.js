/** Mensajes de validación HTML5 en español para formularios del agricultor. */

export function aplicarMensajeValidacion(event) {
  const input = event.target;
  if (!(input instanceof HTMLInputElement) && !(input instanceof HTMLTextAreaElement) && !(input instanceof HTMLSelectElement)) {
    return;
  }
  if (input.validity.valueMissing) {
    input.setCustomValidity("Completa este campo.");
    return;
  }
  if (input.validity.typeMismatch) {
    input.setCustomValidity("Revisa el formato del valor ingresado.");
    return;
  }
  if (input.validity.tooShort) {
    const minimo = input.minLength > 0 ? input.minLength : 8;
    input.setCustomValidity(`Usa al menos ${minimo} caracteres.`);
    return;
  }
  input.setCustomValidity("");
}

export function limpiarMensajeValidacion(event) {
  const input = event.target;
  if (input && typeof input.setCustomValidity === "function") {
    input.setCustomValidity("");
  }
}
