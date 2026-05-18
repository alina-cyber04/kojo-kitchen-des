from pydantic import BaseModel, Field, model_validator


class SimulationConfig(BaseModel):
    """Parámetros del modelo Kojo's Kitchen.

    Objeto inmutable (frozen=True) que centraliza todos los valores numéricos
    del problema. El resto del código lee exclusivamente desde esta instancia.

    Attributes:
        day_duration: Duración total del día en minutos.
        peak1_start: Inicio del primer período pico (min).
        peak1_end: Fin del primer período pico (min).
        peak2_start: Inicio del segundo período pico (min).
        peak2_end: Fin del segundo período pico (min).
        lambda_peak: Tasa de llegadas en hora pico (clientes/min).
        lambda_off_peak: Tasa de llegadas fuera de hora pico (clientes/min).
        sandwich_min: Tiempo mínimo de preparación de sandwich (min).
        sandwich_max: Tiempo máximo de preparación de sandwich (min).
        sushi_min: Tiempo mínimo de preparación de sushi (min).
        sushi_max: Tiempo máximo de preparación de sushi (min).
        p_sandwich: Probabilidad de que un cliente pida sandwich.
        base_staff: Número de empleados activos durante todo el día.
        extra_staff: Empleados adicionales incorporados solo en hora pico.
        n_replications: Número de réplicas por experimento.
        seed: Semilla base para los generadores de números aleatorios.
    """

    # ── Horario (minutos desde apertura: 0 = 10:00am, 660 = 9:00pm) ──
    day_duration:    float = Field(default=660.0, gt=0)

    # Fronteras de hora pico
    peak1_start:     float = Field(default=90.0,  ge=0)   # 11:30am
    peak1_end:       float = Field(default=210.0, ge=0)   # 1:30pm
    peak2_start:     float = Field(default=420.0, ge=0)   # 5:00pm
    peak2_end:       float = Field(default=540.0, ge=0)   # 7:00pm

    # ── Proceso de llegadas ───────────────────────────────────────────
    lambda_peak:     float = Field(default=0.30, gt=0)    # clientes/min en pico
    lambda_off_peak: float = Field(default=0.17, gt=0)    # clientes/min fuera de pico

    # ── Tiempos de servicio Uniforme[min, max] en minutos ─────────────
    sandwich_min:    float = Field(default=3.0, ge=0)
    sandwich_max:    float = Field(default=5.0, gt=0)
    sushi_min:       float = Field(default=5.0, ge=0)
    sushi_max:       float = Field(default=8.0, gt=0)

    # ── Tipo de cliente ───────────────────────────────────────────────
    p_sandwich:      float = Field(default=0.5, ge=0.0, le=1.0)  # probabilidad de sandwich

    # ── Personal ──────────────────────────────────────────────────────
    base_staff:      int   = Field(default=2, ge=1)   # empleados todo el dia
    extra_staff:     int   = Field(default=0, ge=0)   # empleados adicionales en pico

    # ── Configuracion del experimento ─────────────────────────────────
    n_replications:  int   = Field(default=30, ge=1)
    seed:            int   = Field(default=42, ge=0)

    # Inmutabilidad: una vez creado no se puede modificar ningun campo
    model_config = {"frozen": True}

    # ── Validaciones cruzadas ─────────────────────────────────────────
    @model_validator(mode="after")
    def _validate_ranges(self):
        if self.sandwich_max <= self.sandwich_min:
            raise ValueError("sandwich_max debe ser mayor que sandwich_min")
        if self.sushi_max <= self.sushi_min:
            raise ValueError("sushi_max debe ser mayor que sushi_min")
        if self.peak1_end <= self.peak1_start:
            raise ValueError("peak1_end debe ser mayor que peak1_start")
        if self.peak2_end <= self.peak2_start:
            raise ValueError("peak2_end debe ser mayor que peak2_start")
        return self

    # ── Metodos de consulta ───────────────────────────────────────────
    def is_peak(self, t: float) -> bool:
        """Indica si el tiempo t cae dentro de un período pico.

        Args:
            t: Tiempo en minutos desde la apertura.

        Returns:
            True si t pertenece al primer o segundo período pico.
        """
        return (self.peak1_start <= t < self.peak1_end or
                self.peak2_start <= t < self.peak2_end)

    def lambda_at(self, t: float) -> float:
        """Devuelve la tasa de llegadas vigente en el tiempo t.

        Args:
            t: Tiempo en minutos desde la apertura.

        Returns:
            lambda_peak si t es hora pico, lambda_off_peak en caso contrario.
        """
        return self.lambda_peak if self.is_peak(t) else self.lambda_off_peak

    def staff_at(self, t: float) -> int:
        """Devuelve el número de empleados activos en el tiempo t.

        Args:
            t: Tiempo en minutos desde la apertura.

        Returns:
            Suma de empleados base y extra (si es hora pico).
        """
        return self.base_staff + (self.extra_staff if self.is_peak(t) else 0)


# ── Escenarios predefinidos del proyecto ──────────────────────────────

# Escenario A: situacion actual — 2 empleados todo el dia
SCENARIO_A = SimulationConfig(
    base_staff=2,
    extra_staff=0,
)

# Escenario B: alternativa — 2 empleados + 1 extra en horas pico
SCENARIO_B = SimulationConfig(
    base_staff=2,
    extra_staff=1,
)
