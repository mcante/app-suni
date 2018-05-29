import uuid
import qrcode
from io import BytesIO
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from easy_thumbnails import fields as et_fields

from apps.crm import models as crm_m


class EntradaTipo(models.Model):

    """Para indicar el tipo de :class:`Entrada`.
    El campo `contable` indica que los detalles de entrada deben asignar precio.
    """

    nombre = models.CharField(max_length=25)
    contable = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tipo de entrada"
        verbose_name_plural = "Tipos de entrada"

    def __str__(self):
        return self.nombre


class EntradaEstado(models.Model):

    """Para indicar si está en creación, completada o cancelada.
    """

    nombre = models.CharField(max_length=45)

    class Meta:
        verbose_name = "Estado de entrada"
        verbose_name_plural = "Estados de entrada"

    def __str__(self):
        return self.nombre


class Entrada(models.Model):

    """Cualquier vía por la cual puede ingresar equipo al inventario.
    """

    tipo = models.ForeignKey(EntradaTipo, on_delete=models.PROTECT, related_name='entradas')
    fecha = models.DateField()
    en_creacion = models.BooleanField(default=True)
    creada_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='entradas_creadas')
    recibida_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='entradas_recibidas')
    proveedor = models.ForeignKey(crm_m.Donante, on_delete=models.PROTECT, related_name='entradas')

    class Meta:
        verbose_name = "Entrada"
        verbose_name_plural = "Entradas"

    def __str__(self):
        return str(self.id)

    @property
    def descontado(self):
        return self.subtotal - sum(d.monto for d in self.descuentos.all())

    @property
    def subtotal(self):
        return sum(d.precio_subtotal for d in self.detalles.all())

    @property
    def total(self):
        return sum(d.precio_total for d in self.detalles.all())

    def get_absolute_url(self):
        return reverse_lazy('entrada_update', kwargs={'pk': self.id})


class DispositivoTipo(models.Model):

    """Tipo de un :class:`Dispositivo`s
    En caso de que se marque `usa_triage` como `True`, el `slug` debe coincidir con
    los SLUG disponibles en los modelos que heredan :class:`Dispositivo`.
    """

    tipo = models.CharField(max_length=20)
    slug = models.SlugField(unique=True)
    usa_triage = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tipo de dispositivo"
        verbose_name_plural = "Tipos de dispositivo"
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.tipo

    def save(self, *args, **kwargs):
        """Valida que los los :class:`DispositivoTipo` que `usa_triage` tengan un `slug` valido.
        """
        if self.usa_triage:
            lista_slug = [m.SLUG_TIPO for m in Dispositivo.__subclasses__()]
            if self.slug not in lista_slug:
                raise ValidationError(
                    ('El slug ingresado no coincide con los disponibles. Las opciones son: {}'.format(lista_slug)),
                    code='entrada_precio_total')
        super(DispositivoTipo, self).save(*args, **kwargs)


class EntradaDetalle(models.Model):

    """Detalle que indica la cantidad de cada tipo de equipo que ingresa en la :class:`Entrada`.
    Los campos de contabilidad indican el precio al ingresa el equipo cuando la entrada es una compra.
    El usuario ingresa el subtotal, el `precio_unitario` será calculado al dividir `precio_subtotal` / `total`.
    Los descuentos que se apliquen a la Entrada afectarán en el `precio_unitario`, por lo que ese dato
    se almacena en `precio_descontado`.

    El `precio_total` se calcula a partir de `precio_descontado` * `total`.
    """

    # Campos sobre inventario
    entrada = models.ForeignKey(Entrada, on_delete=models.CASCADE, related_name='detalles')
    tipo_dispositivo = models.ForeignKey(DispositivoTipo, on_delete=models.PROTECT, related_name='detalles_entrada')
    util = models.PositiveIntegerField(default=0)
    repuesto = models.PositiveIntegerField(default=0)
    desecho = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField()

    # Campos sobre contabilidad
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    precio_subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    precio_descontado = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    precio_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Registro
    creado_por = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Detalle de entrada"
        verbose_name_plural = "Detalles de entrada"

    def __str__(self):
        return '{entrada} - {tipo}'.format(
            entrada=self.entrada,
            tipo=self.tipo_dispositivo)

    def save(self, *args, **kwargs):
        """Se debe validar que el detalle de una entrada que involucre precio, por ejemplo, una compra,
        incluya el precio total.

        Los valores de los campos `precio_unitario` y `precio_descontado` pueden cambiar dependiendo de
        los descuentos que hayan sido aplicados a la entrada.
        El cálculo de todos los campos se realiza desde las funciones definidas en `signals.py`.
        """
        if self.entrada.tipo.contable and not self.precio_subtotal:
            raise ValidationError(
                'El tipo de entrada requiere un precio total', code='entrada_precio_total')
        super(EntradaDetalle, self).save(*args, **kwargs)

    def crear_dispositivos(self, util=None):
        if util is None:
            util = self.util
        try:
            modelo = [
                f.related_model for f in Dispositivo._meta.get_fields()
                if f.one_to_one and f.related_model.SLUG_TIPO == self.tipo_dispositivo.slug
            ]
            modelo = modelo[0]
            total = 0
            for _ in range(0, util):
                nuevo = modelo(entrada=self.entrada, tipo=self.tipo_dispositivo)
                nuevo.save()
                total = total + 1
        except KeyError as e:
            raise e
        return total

    def get_absolute_url(self):
        return self.entrada.get_absolute_url()


class DescuentoEntrada(models.Model):
    entrada = models.ForeignKey(Entrada, on_delete=models.CASCADE, related_name='descuentos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "DescuentoEntrada"
        verbose_name_plural = "DescuentoEntradas"

    def __str__(self):
        return str(self.entrada)

    def get_absolute_url(self):
        return self.entrada.get_absolute_url()


class DispositivoEstado(models.Model):

    """Estado de un :class:`Dispositivo`. Indica que el dispositivo puede estar en cualquiera de los siguientes estados:
        - Pendiente: aun no ha sido reparado ni desechado
        - Bueno: ya fue reparado
        - Desechado: ha sido desechado por un técnico
        - Entregado: enviado a una escuela
    """

    estado = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Estado de dispositivo"
        verbose_name_plural = "Estados de dispositivo"

    def __str__(self):
        return self.estado


class DispositivoEtapa(models.Model):

    """Etapa de un :class:`Dispositivo`. Indica la parte del proceso de manufactura por la que puede pasar el dispositivo:
        - Almacenado en bodega
        - Tránsito
        - Control de calidad
        - Desechado
        - Listo
        - Entregado

    El campo de estados disponibles indica qué :class:`DispositivoEstado` admite este proceso.
    """

    proceso = models.CharField(max_length=30)
    estados_disponibles = models.ManyToManyField(DispositivoEstado)

    class Meta:
        verbose_name = "Etapa de dispositivo"
        verbose_name_plural = "Etapas de dispositivo"

    def __str__(self):
        return self.proceso


class DispositivoMarca(models.Model):

    """Marca de un :class:`Dispositivo`
    """

    marca = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Marca de dispositivo"
        verbose_name_plural = "Marcas de dispositivo"

    def __str__(self):
        return self.marca


class DispositivoModelo(models.Model):

    """Modelo de un :class:`Dispositivo`
    """

    modelo = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Modelo de dispositivo"
        verbose_name_plural = "Modelos de dispositivo"

    def __str__(self):
        return self.modelo


class Pasillo(models.Model):
    pass

    def __str__(self):
        return str(self.id)

    def tarimas(self):
        return Tarima.objects.filter(sector__nivel__pasillo=self)

    def dispositivo(self):
        return Dispositivo.objects.filter(tarima__sector__nivel__pasillo=self)


class Nivel(models.Model):
    nivel = models.CharField(max_length=1)
    pasillo = models.ForeignKey(Pasillo, on_delete=models.PROTECT, related_name='niveles')

    def __str__(self):
        return '{}{}'.format(self.pasillo, self.nivel)

    def tarimas(self):
        return Tarima.objects.filter(sector__nivel=self)


class Sector(models.Model):
    sector = models.IntegerField(null=False)
    nivel = models.ForeignKey(Nivel, related_name='sectores')
    codigo_qr = et_fields.ThumbnailerImageField(upload_to='qr_sector', blank=True, null=True, editable=False)

    def __str__(self):
        return '{nivel}-{sector}'.format(nivel=self.nivel, sector=self.sector)

    def get_absolute_url(self):
        return reverse_lazy('sector_update', kwargs={'pk': self.id})

    def save(self, *args, **kwargs):
        super(Sector, self).save(*args, **kwargs)
        if not self.codigo_qr:
            self.crear_qrcode()
            super(Sector, self).save(*args, **kwargs)

    def crear_qrcode(self):
        """Genera le código QR para apuntar a la id del sector
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=6,
            border=1,
        )
        qr.add_data(self.id)
        qr.make(fit=True)
        img = qr.make_image()
        buffer = BytesIO()
        img.save(buffer)
        filename = 'sector-{}.png'.format(self.id)
        filebuffer = InMemoryUploadedFile(buffer, None, filename, 'image/png', buffer.getbuffer().nbytes, None)
        self.codigo_qr.save(filename, filebuffer)


class Tarima(models.Model):
    sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='tarimas'
    )
    codigo_qr = et_fields.ThumbnailerImageField(upload_to='qr_tarima', blank=True, null=True)

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        super(Tarima, self).save(*args, **kwargs)
        if not self.codigo_qr:
            self.crear_qrcode()
            super(Tarima, self).save(*args, **kwargs)

    def crear_qrcode(self):
        """Genera le código QR para apuntar a la id de la tarima
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=6,
            border=1,
        )
        qr.add_data(self.id)
        qr.make(fit=True)
        img = qr.make_image()
        buffer = BytesIO()
        img.save(buffer)
        filename = 'tarima-{}.png'.format(self.id)
        filebuffer = InMemoryUploadedFile(buffer, None, filename, 'image/png', buffer.getbuffer().nbytes, None)
        self.codigo_qr.save(filename, filebuffer)


class Dispositivo(models.Model):

    """Cualquier elemento almacenado en la base de datos de inventario que puede ser entregado a una escuela.
    No debe existir una instancia de este modelo sin un objeto heredado del mismo.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triage = models.SlugField(unique=True, blank=True, editable=False)
    tipo = models.ForeignKey(DispositivoTipo, on_delete=models.CASCADE)
    entrada = models.ForeignKey(Entrada, on_delete=models.PROTECT, related_name='dispositivos')
    estado = models.ForeignKey(DispositivoEstado, on_delete=models.CASCADE, null=True, editable=False)
    etapa = models.ForeignKey(DispositivoEtapa, on_delete=models.PROTECT, null=True, editable=False)

    marca = models.ForeignKey(DispositivoMarca, on_delete=models.CASCADE, null=True, blank=True)
    modelo = models.ForeignKey(DispositivoModelo, on_delete=models.CASCADE, null=True, blank=True)
    serie = models.CharField(max_length=80, null=True, blank=True)
    codigo_qr = et_fields.ThumbnailerImageField(upload_to='qr_dispositivo', blank=True, null=True)
    tarima = models.ForeignKey(Tarima, on_delete=models.PROTECT, blank=True, null=True, related_name='dispositivos')

    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"
        indexes = [
            models.Index(fields=['triage']),
        ]

    def __str__(self):
        return str(self.triage)

    def get_absolute_url(self):
        return self.cast().get_absolute_url()

    def cast(self):
        """Se encarga de obtener el dispositivo del modelo que ha heredado este objeto.
        Por ejemplo, el CPU-1, M-3, etc.
        """
        for name in dir(self):
            try:
                attr = getattr(self, name)
                if isinstance(attr, self.__class__) and type(attr) != type(self):
                    return attr
            except:
                print("a")

    def crear_qrcode(self):
        """Genera le código QR para apuntar a la id del dispositivo
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=6,
            border=1,
        )
        qr.add_data(self.id)
        img = qr.make(fit=True).make_image()
        buffer = BytesIO()
        img.save(buffer)
        filename = 'dispositivo-{}.png'.format(self.id)
        filebuffer = InMemoryUploadedFile(buffer, None, filename, 'image/png', buffer.getbuffer().nbytes, None)
        self.codigo_qr.save(filename, filebuffer)


class DispositivoFalla(models.Model):
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE, related_name='fallas')
    descripcion_falla = models.TextField(verbose_name='Descripción de la falla')
    descripcion_solucion = models.TextField(null=True, blank=True, verbose_name='Descripción de la solución')
    fecha_inicio = models.DateTimeField(default=timezone.now, verbose_name='Fecha de inicio')
    fecha_fin = models.DateTimeField(blank=True, verbose_name='Fecha de fin', null=True)
    terminada = models.BooleanField(default=False, blank=True)
    reportada_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='fallas_reportadas')
    reparada_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='fallas_reparadas',
        null=True,
        blank=True)

    class Meta:
        verbose_name = "DispositivoFalla"
        verbose_name_plural = "DispositivoFallas"

    def __str__(self):
        return 'F-{pk}'.format(pk=self.id)


class SoftwareTipo(models.Model):

    """Para indicar si es aplicación, sistema operativo, etc.
    """

    tipo = models.CharField(max_length=25)

    class Meta:
        verbose_name = "Tipo de software"
        verbose_name_plural = "Tipos de software"

    def __str__(self):
        return self.tipo


class Software(models.Model):

    """Cualquier software que se pueda instalar en un :class:`Dispositivo` de cualquier tipo.
    """

    nombre = models.CharField(max_length=100)
    tipo = models.ForeignKey(SoftwareTipo, on_delete=models.CASCADE)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Software"
        verbose_name_plural = "Software"

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse_lazy('software_detail', kwargs={'pk': self.id})


class VersionSistema(models.Model):

    """Imagen de un sistema instalable en un :class:`Dispositivo`.
    Incluye el sistema operativo y los programas o aplicaciones que se instalen.
    """

    nombre = models.CharField(max_length=55)
    so = models.ForeignKey(Software, on_delete=models.CASCADE, related_name='versiones')
    software = models.ManyToManyField(Software, blank=True)

    class Meta:
        verbose_name = "Versión de sistema"
        verbose_name_plural = "Versiones de sistema"

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse_lazy('versionsistema_detail', kwargs={'pk': self.id})


class PuertoTipo(models.Model):
    nombre = models.CharField(max_length=30)

    class Meta:
        verbose_name = "Tipo de puerto"
        verbose_name_plural = "Tipos de puerto"

    def __str__(self):
        return self.nombre


class DispositivoPuerto(models.Model):

    """Puerto de cualquier tipo de :class:`Dispositivo`.
    """

    nombre = models.CharField(max_length=15)
    tipo = models.ForeignKey(PuertoTipo, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Puerto"
        verbose_name_plural = "Puertos"

    def __str__(self):
        return self.nombre


class DispositivoMedida(models.Model):

    """Medida de cualquier tipo de :class:`Dispositivo` (GB, GH, Mbps, etc)
    """

    nombre = models.CharField(max_length=15)

    class Meta:
        verbose_name = "Medida"
        verbose_name_plural = "Medidas"

    def __str__(self):
        return self.nombre


class Teclado(Dispositivo):
    SLUG_TIPO = 'T'
    indice = models.PositiveIntegerField(editable=False, unique=True)
    puerto = models.ForeignKey(
        DispositivoPuerto,
        on_delete=models.CASCADE,
        related_name='teclados',
        null=True,
        blank=True)

    class Meta:
        verbose_name = "Teclado"
        verbose_name_plural = "Teclados"
        ordering = ['indice']
        indexes = [
            models.Index(fields=['indice']),
        ]
        db_table = 'dispositivo_teclado'

    def __str__(self):
        return self.triage


class MouseTipo(models.Model):

    """Para indicar si es mecánico, óptico o cualquier tipo futuro.
    """

    tipo = models.CharField(max_length=15)

    class Meta:
        verbose_name = "Tipo de mouse"
        verbose_name_plural = "Tipos de mouse"

    def __str__(self):
        return self.tipo


class Mouse(Dispositivo):
    SLUG_TIPO = 'S'
    indice = models.PositiveIntegerField(editable=False, unique=True)
    puerto = models.ForeignKey(
        DispositivoPuerto,
        on_delete=models.CASCADE,
        related_name='mouses',
        null=True,
        blank=True)
    tipo_mouse = models.ForeignKey(MouseTipo, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = "Mouse"
        verbose_name_plural = "Mouses"
        ordering = ['indice']
        indexes = [
            models.Index(fields=['indice']),
        ]
        db_table = 'dispositivo_mouse'

    def __str__(self):
        return self.triage


class HDD(Dispositivo):
    SLUG_TIPO = 'HDD'
    indice = models.PositiveIntegerField(editable=False, unique=True)
    puerto = models.ForeignKey(
        DispositivoPuerto,
        on_delete=models.CASCADE,
        related_name='hdds',
        null=True,
        blank=True)
    capacidad = models.PositiveIntegerField(null=True, blank=True)
    medida = models.ForeignKey(DispositivoMedida, null=True, blank=True)

    class Meta:
        verbose_name = "HDD"
        verbose_name_plural = "HDDs"
        ordering = ['indice']
        indexes = [
            models.Index(fields=['indice']),
        ]
        db_table = 'dispositivo_hdd'

    def __str__(self):
        return self.triage

    @property
    def en_uso(self):
        """Indica si fue asignado a un :class:`CPU` o :class:`Laptop`

        Returns:
            bool
        """
        return self.cpus.count() > 0 or self.laptops.count() > 0


class Procesador(models.Model):
    nombre = models.CharField(max_length=25)

    class Meta:
        verbose_name = "Procesador"
        verbose_name_plural = "Procesadores"

    def __str__(self):
        return self.nombre


class Tablet(Dispositivo):
    SLUG_TIPO = 'B'
    indice = models.PositiveIntegerField(editable=False, unique=True)
    version_sistema = models.ForeignKey(VersionSistema, related_name='versiones_tablets', null=True, blank=True)
    so_id = models.ForeignKey(Software, related_name='so_tablets', null=True, blank=True)
    almacenamiento = models.PositiveIntegerField(null=True, blank=True)
    medida_almacenamiento = models.ForeignKey(
        DispositivoMedida,
        blank=True,
        null=True,
        related_name='almacenamiento_tablets')
    pulgadas = models.PositiveIntegerField(null=True, blank=True)
    procesador = models.ForeignKey(Procesador, blank=True, null=True)
    ram = models.PositiveIntegerField(null=True, blank=True)
    medida_ram = models.ForeignKey(DispositivoMedida, null=True, blank=True, related_name='ram_tables')
    almacenamiento_externo = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tablet"
        verbose_name_plural = "Tablets"
        ordering = ['indice']
        indexes = [
            models.Index(fields=['indice']),
        ]
        db_table = 'dispositivo_tablet'

    def __str__(self):
        return self.triage


class MonitorTipo(models.Model):

    """Para indicar si un :class:`Monitor` puede ser CRT, LCD, LED.
    """

    tipo = models.CharField(max_length=15)

    class Meta:
        verbose_name = "Tipo de monitor"
        verbose_name_plural = "Tipos de monitor"

    def __str__(self):
        return self.tipo


class Monitor(Dispositivo):
    SLUG_TIPO = 'M'
    indice = models.PositiveIntegerField(editable=False, unique=True)
    tipo_monitor = models.ForeignKey(MonitorTipo, on_delete=models.PROTECT, null=True, blank=True)
    puerto = models.ForeignKey(
        DispositivoPuerto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='monitores')
    pulgadas = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)

    class Meta:
        verbose_name = "Monitor"
        verbose_name_plural = "Monitores"
        ordering = ['indice']
        indexes = [
            models.Index(fields=['indice']),
        ]
        db_table = 'dispositivo_monitor'

    def __str__(self):
        return self.triage

    def get_absolute_url(self):
        return reverse_lazy('monitor_detail', kwargs={'triage': self.triage})


class CPU(Dispositivo):
    SLUG_TIPO = 'CPU'
    indice = models.PositiveIntegerField(editable=False, unique=True)
    procesador = models.ForeignKey(Procesador, on_delete=models.PROTECT, null=True, blank=True)
    version_sistema = models.ForeignKey(VersionSistema, on_delete=models.PROTECT, null=True, blank=True)
    disco_duro = models.ForeignKey(HDD, on_delete=models.PROTECT, null=True, blank=True, related_name='cpus')
    ram = models.PositiveIntegerField(null=True, blank=True)
    ram_medida = models.ForeignKey(DispositivoMedida, null=True, blank=True)

    class Meta:
        verbose_name = "CPU"
        verbose_name_plural = "CPUs"
        ordering = ['indice']
        indexes = [
            models.Index(fields=['indice']),
        ]
        db_table = 'dispositivo_cpu'

    def __str__(self):
        return self.triage


class Laptop(Dispositivo):
    SLUG_TIPO = 'L'
    indice = models.PositiveIntegerField(editable=False, unique=True)
    procesador = models.ForeignKey(Procesador, on_delete=models.PROTECT, null=True, blank=True)
    version_sistema = models.ForeignKey(VersionSistema, on_delete=models.PROTECT, null=True, blank=True)
    disco_duro = models.ForeignKey(HDD, on_delete=models.PROTECT, null=True, blank=True, related_name='laptops')
    ram = models.PositiveIntegerField(null=True, blank=True)
    ram_medida = models.ForeignKey(DispositivoMedida, null=True, blank=True)
    pulgadas = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)

    class Meta:
        verbose_name = "Laptop"
        verbose_name_plural = "Laptops"
        ordering = ['indice']
        indexes = [
            models.Index(fields=['indice']),
        ]
        db_table = 'dispositivo_laptop'

    def __str__(self):
        return self.triage


class TipoRed(models.Model):
    nombre = models.CharField(max_length=45)

    class Meta:
        verbose_name = "Tipo de dispositivo de red"
        verbose_name_plural = "Tipos de dispositivos de red"

    def __str__(self):
        return self.nombre


class DispositivoRed(Dispositivo):
    SLUG_TIPO = 'R'
    indice = models.PositiveIntegerField(editable=False, unique=True)
    cantidad_puertos = models.PositiveIntegerField(null=True, blank=True)
    puerto = models.ForeignKey(DispositivoPuerto, null=True, blank=True)
    velocidad = models.PositiveIntegerField(null=True, blank=True)
    velocidad_medida = models.ForeignKey(DispositivoMedida, null=True, blank=True)

    class Meta:
        verbose_name = "Dispositivo de red"
        verbose_name_plural = "Dispositivos de red"

    def __str__(self):
        return self.triage


class RepuestoEstado(models.Model):

    """Indica si el repuesto puede ser:
    - Almacenaje
    - Utilizado
    - Desechado
    """

    nombre = models.CharField(max_length=25)

    class Meta:
        verbose_name = "Estado de repuesto"
        verbose_name_plural = "Estados de repuesto"

    def __str__(self):
        return self.nombre


class Repuesto(models.Model):
    entrada = models.ForeignKey(Entrada, on_delete=models.CASCADE, related_name='repuestos')
    tipo = models.ForeignKey(DispositivoTipo, on_delete=models.PROTECT, related_name='repuestos')
    estado = models.ForeignKey(RepuestoEstado, on_delete=models.PROTECT)
    descripcion = models.TextField(null=True, blank=True)
    disponible = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Repuesto"
        verbose_name_plural = "Repuestos"

    def __str__(self):
        return 'R-{}'.format(self.id)


class DispositivoRepuesto(models.Model):
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(default=timezone.now)
    asignado_por = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Repuesto de dispositivo"
        verbose_name_plural = "Repuestos de dispositivo"

    def __str__(self):
        return '{} -> {}'.format(self.repuesto, self.dispositivo)


class DesechoEmpresa(models.Model):
    nombre = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Empresa de desecho"
        verbose_name_plural = "Empresas de desecho"

    def __str__(self):
        return self.nombre


class DesechoSalida(models.Model):
    fecha = models.DateField(default=timezone.now)
    empresa = models.ForeignKey(DesechoEmpresa, on_delete=models.PROTECT, related_name='salidas')
    precio_total = models.DecimalField(max_digits=12, decimal_places=2)
    peso = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Peso (libras)')
    creado_por = models.ForeignKey(User, on_delete=models.PROTECT)
    observaciones = models.TextField(null=True, blank=True)
    en_creacion = models.BooleanField(default=True, blank=True, verbose_name='En creación')

    class Meta:
        verbose_name = "Salida de desecho"
        verbose_name_plural = "Salidas de desecho"

    def __str__(self):
        return str(self.id)


class DesechoDetalle(models.Model):
    desecho = models.ForeignKey(DesechoSalida, on_delete=models.PROTECT, related_name='detalles')
    entrada_detalle = models.ForeignKey(
        EntradaDetalle,
        on_delete=models.PROTECT,
        null=True,
        blank=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Detalle de salida de desecho"
        verbose_name_plural = "Detalles de salida de desecho"

    def __str__(self):
        return '{desecho} {entrada}'.format(
            desecho=self.desecho,
            entrada=self.entrada_detalle)

# class Paquete(models.Model):
#     salida = models.PositiveIntegerField()
#     indice = models.PositiveIntegerField()
#     creado_por = models.ForeignKey(User, on_delete=models.PROTECT)
#     equipo = models.BooleanField(default=True)

#     class Meta:
#         verbose_name = "Paquete"
#         verbose_name_plural = "Paquetes"

#     def __str__(self):
#         return str(self.salida)


# class DispositivoPaquete(models.Model):
#     dispositivo = models.ForeignKey(Dispositivo, on_delete=models.PROTECT)
#     paquete = models.ForeignKey(Paquete, on_delete=models.PROTECT)
#     fecha_creacion = models.DateTimeField(default=timezone.now)
#     asignado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='paquetes_asignados')
#     fecha_aprobacion = models.DateTimeField(null=True, blank=True)
#     aprobado = models.BooleanField(default=False)
#     aprobado_por = models.ForeignKey(
#         User,
#         on_delete=models.PROTECT,
#         null=True,
#         blank=True,
#         related_name='paquetes_aprobados')

#     class Meta:
#         verbose_name = "DispositivoPaquete"
#         verbose_name_plural = "DispositivoPaquetes"

#     def __str__(self):
#         return '{} -> {}'.format(self.dispositivo, self.paquete)


