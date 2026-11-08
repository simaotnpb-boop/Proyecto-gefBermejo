-- =========================================================================
-- ESQUEMA Y DATOS PARA SUPABASE - REGISTRO DE ASISTENCIA Y CONTROL QR
-- PROYECTO GEF BERMEJO (123 PARTICIPANTES)
-- =========================================================================
-- Instrucciones para ejecutar en Supabase:
-- 1. Ve a tu panel en https://supabase.com
-- 2. Entra a tu proyecto y selecciona "SQL Editor" en el menú izquierdo.
-- 3. Pega todo este código y haz clic en "RUN".
-- =========================================================================

-- 1. CREAR LA TABLA DE ASISTENCIA
CREATE TABLE IF NOT EXISTS public.asistencia_gef_bermejo (
    numero INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    institucion TEXT,
    estado_general TEXT DEFAULT 'Pendiente',
    dia_1 TEXT DEFAULT 'Ausente',
    dia_1_fecha_hora TEXT DEFAULT '',
    dia_1_observacion TEXT DEFAULT '',
    dia_2 TEXT DEFAULT 'Ausente',
    dia_2_fecha_hora TEXT DEFAULT '',
    dia_2_observacion TEXT DEFAULT '',
    dia_3 TEXT DEFAULT 'Ausente',
    dia_3_fecha_hora TEXT DEFAULT '',
    dia_3_observacion TEXT DEFAULT '',
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 2. HABILITAR ROW LEVEL SECURITY (RLS) Y PERMISOS PÚBLICOS
ALTER TABLE public.asistencia_gef_bermejo ENABLE ROW LEVEL SECURITY;

-- Permitir lectura pública (con anon key)
CREATE POLICY "Permitir lectura publica" 
ON public.asistencia_gef_bermejo 
FOR SELECT 
USING (true);

-- Permitir inserción y actualización pública (con anon key)
CREATE POLICY "Permitir actualizacion publica" 
ON public.asistencia_gef_bermejo 
FOR UPDATE 
USING (true);

CREATE POLICY "Permitir insercion publica" 
ON public.asistencia_gef_bermejo 
FOR INSERT 
WITH CHECK (true);

-- 3. HABILITAR REALTIME (opcional para ver actualizaciones en vivo)
ALTER PUBLICATION supabase_realtime ADD TABLE public.asistencia_gef_bermejo;

-- 4. INSERTAR LOS 123 ASISTENTES CONFIRMADOS (SI NO EXISTEN YA)
INSERT INTO public.asistencia_gef_bermejo (numero, nombre, institucion) VALUES
(1, 'Jorge Edgardo Castellano', 'Presidente del Directorio de la Comisión Regional del Río Bermejo (COREBE), Argentina'),
(2, 'Rosa Delia Gómez Durán', 'Ministra Plenipotenciaria. Representante Política Alterna de Argentina ante el Comité Intergubernamental Coordinador de los Países de la Cuenca del Plata (CIC)'),
(3, 'Marcelo Julian Borsellino', ''),
(4, 'Vanesa Martinero ', ''),
(5, 'Ignacio Enriquez', 'Representante Técnico Alterno de Argentina ante el CIC de la Cuenca del Plata'),
(6, 'Carlos Paz Ide', 'Viceministro de Relaciones Exteriores y Seguridad Transnacional del Ministerio de Relaciones Exteriores de Bolivia.'),
(7, 'Javier Vizcarra', 'Embajador. Representante Político Alterno de Bolivia ante el CIC de la Cuenca del Plata.'),
(8, 'Aida Elva Chura Apaza', 'Profesional de la Cuenca del Plata del Ministerio de Relaciones Exteriores de Bolivia'),
(9, 'César Alfredo Echeverría Jáuregui', 'Jefe de la Unidad de Aguas Internacionales Transfronterizas del Ministerio de Relaciones Exteriores de Bolivia'),
(10, 'Guillermo Antonio Sadir', 'Secretario de Planes, Programas y Proyectos; representante de la Provincia de Jujuy ante COREBE'),
(11, 'Mark Lambrides', 'Director del Departamento de Desarrollo Sostenible (DDS) de la Organización de los Estados Americanos (OEA'),
(12, 'Delfina Iervolino', 'Oficial de Proyecto del Departamento de Desarrollo Sostenible (DDS) de la OEA'),
(13, 'Sebastian Izquierdo', 'Consultor del Departamento de Desarrollo Sostenible (DDS) de la OEA.'),
(14, 'Adriana Sandoval', 'Consultora del Departamento de Desarrollo Sostenible (DDS) de la OEA.'),
(15, 'Cecilia Guerra', 'Ejecutiva Principal De Acción Climática Y Ambiente CAF'),
(16, 'Guillermo Antonio Sadir', 'Director Provincial de Recursos Hídricos del Gobierno de la Provincia de Jujuy'),
(17, 'Luz Melon ', 'Cónsul de la República Argentina en Tarija y delegada argentina vinculada a COREBE/COBINABE'),
(18, 'Diego Ávila Navajas', 'Presidente de la Cámara de Senadores de la Asamblea Legislativa Plurinacional de Bolivia.'),
(19, 'Viviana Mariscal Montaño', 'Viceministra de Seguridad Hídrica, Agua, Saneamiento Básico y Riego en Bolivia'),
(20, 'Noelia Vedia Fernandez ', 'Funcionaria de la Reserva Nacional de Flora y Fauna Tariquía, Servicio Nacional de Áreas Protegidas (SERNAP)'),
(21, 'Enrrique Tejerina Ruiz', 'Reserva Nacional de Flora y Fauna Tariquia - Director'),
(22, 'Marco Antonio Trujillo Garcia ', 'Representante de la Reserva Biológica Cordillera de Sama (SERNAP)'),
(23, 'Gonzalo Ávila Sánchez', 'Vicegobernador del Departamento de Tarija'),
(24, 'Patricio Marcelo Moscoso Pantoja', 'Director de Medio Ambiente y Recursos Naturales del Gobierno Autónomo Departamental de Tarija.'),
(25, 'Ismael Alexander Pantoja Vega', 'Funcionario de la Dirección de Medio Ambiente del Gobierno Autónomo Departamental de Tarija'),
(26, 'Eugenia Magaly Fernandez Mogro ', ''),
(27, 'Carlos Rico Soliz', ''),
(28, 'Omar García Nuñez ', ''),
(29, 'Zulema Paola Chipana Martínez', 'Asambleísta Departamental Por Población De La Provincia Arce'),
(30, 'Juan Adolfo Ortega Santos', 'Asambleísta Departamental Suplente Por Población De La Provincia Arce'),
(31, 'Luis Miguel Sossa Aguilera', 'Asambleísta Departamental de Tarija.'),
(32, 'José Fabián Ochoa Virreira', 'Asambleísta Departamental de Tarija.'),
(33, 'Lic. Álvaro Fernando Trigo Rollano', 'Director de Gestión de la Cooperación y Financiamiento del Gobierno Autónomo Departamental de Tarija'),
(34, 'Anyelo Estrada ', 'Encargado de Medio Ambiente y Gestión de Riesgos Municipio San Lorenzo'),
(35, 'José Renán Justiniano Arce', 'Concejal del Gobierno Autónomo Municipal de Tarija.'),
(36, 'Rivelino Zenteno Victorio', 'Concejal Del Gobierno Autónomo Municipal De Tarija'),
(37, 'Edwin Almendras Vásques', 'Magistrado Tribunal Agroambienta de Bollivia'),
(38, 'Dr. Eduardo Andrés Jordán Pérez', 'Coordinador General de la Fundación FAUTAPO'),
(39, 'Iván Arnold', 'Director Ejecutivo de la organización NATIVA'),
(40, 'Cecilia Cortez Franco', ''),
(41, 'Guido Cortez', 'Director Ejecutivo del Centro de Estudios Regionales de Tarija (CERDET).'),
(42, 'Ricardo Paita Diaz', 'Coordinador General CERDET'),
(43, 'Samuel La Madrid', ''),
(44, 'Sergio Martinez', 'Director Ejecutivo de Esperanza Bolivia.'),
(45, 'Alfonso Blanco Lopez', 'Presidente del Directorio FAO/GEF Guadalquivir'),
(46, 'Pedro Azuga Hurtado', 'FAO GEF Guadalquivir'),
(47, 'Carolina Tejerina Hoyos', 'FAO GEF Guadalquivir'),
(48, 'Pablo Andres Calizaya Gutierrez', 'FAO GEF Guadalquivir'),
(49, 'María Elena Moreira Pereira ', 'FAO GEF Guadalquivir'),
(50, 'Noelia Mollinedo Taboada', 'Directora Ejecutiva Fundación Creamos Juntos'),
(51, 'Marcelo Ferrufino Ugarte ', 'Director Gral. De Bolivia Cero Residuos - Gerente Gral. De Ecoingenieria Integral ER2'),
(52, 'Joaquín Sebastián Ferrufino Catalán ', 'Coodinador Tecnico de Bolivia Cero Residuos'),
(53, 'Daniela Cubas Cossio', 'Coordinadora de Alianzas Estratégicas – Cono Sur'),
(54, 'Natalia Araujo', 'Representante PEW'),
(55, 'Sebastiano Pepe', 'Representante Rewilding Argentina'),
(56, 'María Alejandra Leigue Fernández', 'Representante de la Universidad Católica Boliviana'),
(57, 'Lorena Sánchez Barrero ', 'Representante de la Universidad Católica Boliviana'),
(58, 'Marcelo Segovia Cortez ', 'Representante de la Universidad Autónoma Juan Misael Saracho (UAJMS)'),
(59, 'Jaime Daniel Salas Mercado', 'Vicerrector Académico de la Universidad Privada Domingo Savio (UPDS)'),
(60, 'Eduardo Ibarra', 'Ejecutivo Subcentral Distrito 11 Río Tarija'),
(61, 'José Antonio Ledezma Torrez', 'Presidente del Comité de Monitoreo Socioambiental de los Proyectos Astilleros y Churumas.'),
(62, 'Javier Ávila', 'Gerente de Seguridad, Salud, Medio Ambiente y Relacionamiento Comunitario'),
(63, 'Mauricio Collau Andia', 'Jefe de Relacionamiento Comunitario'),
(64, 'Esteban Gonzalez Bonorino', 'Representante vecinal de la comunidad de La Merced, municipio de Padcaya'),
(65, 'Guillermo Gonzalez Bonorino', 'Consejal por el Municipio de Padcaya'),
(66, 'José Manuel Yáñez López', 'Presidente y Ejecutivo Nacional de los Regantes de Bolivia'),
(67, 'Yovany Quispe', 'Presidente de la Asociación Departamental de Regantes y Sistemas Comunitarios de Agua Potable de Tarija'),
(68, 'Diego Castillo', ''),
(69, 'Alba Litza Gareca Cruz ', ''),
(70, 'leopoldo López Cossio', 'Comite Cívico de Tarija - Asesor'),
(71, 'María René Soruco Campero', 'Gobernador del Departamento de Tarija'),
(72, 'Sergio Lea Plaza', 'Asesor General del Gobierno Autónomo Departamental de Tarija.'),
(73, 'David Castellanos', 'Secretario Departamental de Desarrollo Económico y Medio Ambiente en el Gobierno Autónomo Departamental de Tarija'),
(74, 'Dip. Gabriel Corvera Sittyc', 'Presidente De La Brigada Parlamentaria De Tarija'),
(75, 'Gabriela Pacello Guillén', 'Diputada Nacional de la Asamblea Legislativa Plurinacional de Bolivia.'),
(76, 'Adriana Estefanía Aguirre Castellanos', 'Diputada Nacional Suplente de la Asamblea Legislativa Plurinacional de Bolivia.'),
(77, 'Rubén Horacio Calizaya Gutiérrez', 'Diputado Nacional de la Asamblea Legislativa Plurinacional de Bolivia'),
(78, 'Karina Patricia Liebers Cáceres', 'Diputada Nacional de la Asamblea Legislativa Plurinacional de Bolivia'),
(79, 'José Luis Porcel Marquina', 'Diputado Nacional de la Asamblea Legislativa Plurinacional de Bolivia'),
(80, 'Luis Rodrigo Fuenzalida Cardona', 'Diputado Nacional Suplente de la Asamblea Legislativa Plurinacional de Bolivia.'),
(81, 'Lorena Guiselle Gareca Mealla', 'Diputada Nacional de la Asamblea Legislativa Plurinacional de Bolivia.'),
(82, 'María Isabel Moreno Cortez', 'Senadora Del Estado Plurinacional De Bolivia'),
(83, 'César Mentasti Padilla', 'Senador Del Estado Plurinacional De Bolivia'),
(84, 'Marcela Guerrero Vilca', 'Senadora Suplente del Estado Plurinacional de Bolivia.'),
(85, 'Rolando Vacaflor Gabriel Arana', 'Senador Suplente del Estado Plurinacional de Bolivia.'),
(86, 'Jhonny Marcel Torres Terzo', 'Alcalde del Gobierno Autónomo Municipal de Tarija.'),
(87, 'Fernando Castellanos', 'Secretario Municipal de Medio Ambiente y Gestión de la Cooperación Gobierno Autónomo Municipal de Tarija'),
(88, 'Gilmar Miranda Zutara', 'Alcalde Municipal de Padcaya'),
(89, 'Ing. Darcy Morales ', 'Encargado Unidad de Medio Ambiente Municipio de Padcaya'),
(90, 'José Gira Martínez', 'Alcalde Municipal de Uriondo'),
(91, 'Ing. Juanito Ruiz Sagredo', 'Oficial Mayor de Desarrollo Productivo Municipio de Uriondo'),
(92, 'Joel Isidoro Quisberth Requena', 'Alcalde Municipal de Entre Rios'),
(93, 'Ing. Juvenal Altamirano ', 'Representante de la Unidad de Medio Ambiente y Gestión de Riesgos Entre Rios'),
(94, 'Víctor Hugo Morales Vargas', 'Alcalde Municipal de Bermejo'),
(95, 'Ing. Víctor Mancilla', 'Representante de la Secretaría de Desarrollo Productivo y Medio Ambiente Bermejo'),
(96, 'Ing. Mario Batallanos Morales', 'Alcalde Municipal de Carapari'),
(97, 'Ing. Pablo Reinerio Tapia Romero', 'Responsable de Medio Ambiente y Forestal Municipio de Carapari'),
(98, 'Ing. Marcelo Jesús Zenteno Castrillo', 'Presidente Del Concejo Municipal De Tarija'),
(99, 'Rodrigo Alejandro Calizaya Gutiérrez', 'Secretario Del Concejo Municipal De Tarija'),
(100, 'Carlos Jalil', 'Director Regional de ACLO'),
(101, 'Sergio Criales', 'Director de WWF Bolivia'),
(102, 'Maria Teresa Vargas', 'Directora Ejecutiva de Natura'),
(103, 'Gabriel Baracatt Sabat', 'Presidente del Consejo Directivo de la Fundación Avina'),
(104, 'Jakob Kerstan', 'Representante De La Fundación Konrad Adenauer (Kas) En Bolivia'),
(105, 'David Tecklin', 'Director de Proyecto en el área de Conservación de Tierras y Agua Dulce PEW'),
(106, 'Jürgen Kohlberg de Grandchant', 'Rector de la Sede Tarija de la Universidad Católica Boliviana San Pablo'),
(107, 'María Carolina Soto Montenegro', 'Directora Académica de la Sede Tarija de la Universidad Católica Boliviana San Pablo'),
(108, 'M.Sc. José Luis Narváez Flores', 'Rector Interino de la Universidad Autónoma Juan Misael Saracho (UAJMS) de Tarija'),
(109, 'Sergio Borja Alarcón', 'Rector Nacional de la Universidad Privada Domingo Savio (UPDS).'),
(110, 'Franz Molina Conzelmann', 'Presidente De La Federación De Empresarios Privados De Tarija (FEPT)'),
(111, 'Claudia Jimena Fernández Mercado', 'Directora De La Fundación Coca-Cola Bolivia'),
(112, 'Gerardo Corvera Vargas', 'Vicepresidente del comité de monitoreo'),
(113, 'Héctor Francisco Huanca Gutiérrez', 'Ministro de Relaciones Exteriores del Estado Plurinacional de Bolivia'),
(114, 'Fernando Hugo Aramayo Carrasco', 'Ministro de la Presidencia'),
(115, 'Christian Andrés Morales Burgos', 'Ministro de Economía y Finanzas Públicas'),
(116, 'Ernesto Amílcar Justiniano Hurtado', 'Ministro de Defensa'),
(117, 'Marco Antonio Oviedo Huerta', 'Ministro de Gobierno'),
(118, 'Marcelo Blanco Quintanilla', 'Ministro de Hidrocarburos y Energías'),
(119, 'Mauricio Zamora Liebers', 'Ministro de Obras Públicas, Servicios y Vivienda'),
(120, 'Óscar Mario Justiniano Pinto', 'Ministro de Desarrollo Productivo, Rural y Agua'),
(121, 'Jorge Ernesto Ávila Antelo', 'Viceministro de Medio Ambiente, Biodiversidad, Cambios Climáticos y de Gestión y Desarrollo Forestal'),
(122, 'Adrián Oliva Alcázar', 'Viceministro de Autonomías'),
(123, 'Luis Alberto Pereira Cantos', 'Gerente de Proyectos e Investigación en Yacimientos de Litio Bolivianos (YLB)')
ON CONFLICT (numero) DO NOTHING;

