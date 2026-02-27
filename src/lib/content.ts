export const POLICY_VERSION = "v1.1-2024-05-24";

export const districts = [
  "Centro",
  "Arganzuela",
  "Retiro",
  "Salamanca",
  "Chamartín",
  "Tetuán",
  "Chamberí",
  "Fuencarral-El Pardo",
  "Moncloa-Aravaca",
  "Latina",
  "Carabanchel",
  "Usera",
  "Puente de Vallecas",
  "Moratalaz",
  "Ciudad Lineal",
  "Hortaleza",
  "Villaverde",
  "Villa de Vallecas",
  "Vicálvaro",
  "San Blas-Canillejas",
  "Barajas",
  "Otros",
] as const;

export const districtGroups = [
  {
    key: "central",
    districts: ["Centro", "Arganzuela", "Retiro", "Salamanca", "Chamberí"],
  },
  {
    key: "north",
    districts: [
      "Chamartín",
      "Tetuán",
      "Fuencarral-El Pardo",
      "Hortaleza",
      "Barajas",
    ],
  },
  {
    key: "east",
    districts: [
      "Ciudad Lineal",
      "Moratalaz",
      "Vicálvaro",
      "San Blas-Canillejas",
    ],
  },
  {
    key: "south",
    districts: [
      "Usera",
      "Puente de Vallecas",
      "Villaverde",
      "Villa de Vallecas",
      "Carabanchel",
    ],
  },
  {
    key: "west",
    districts: ["Moncloa-Aravaca", "Latina", "Otros"],
  },
] as const;

export type Language = "Español" | "English";
export type Option = { value: string; label: string };

interface CopySet {
  badge: string;
  eyebrow: string;
  headline: string;
  intro: string;
  stickyCta: string;
  formTitle: string;
  progressLabel: string;
  stepOf: string;
  stepNames: string[];
  nextStep: string;
  previousStep: string;
  name: string;
  namePlaceholder: string;
  wa: string;
  waPlaceholder: string;
  age: string;
  gender: string;
  livingPreference: string;
  budget: string;
  budgetPlaceholder: string;
  rooms: string;
  country: string;
  countryDefault: string;
  countryOptions: Option[];
  language: string;
  languageOptions: Option[];
  urgency: string;
  urgencyOptions: Option[];
  lifestyle: string;
  lifestyleOptions: string[];
  areas: string;
  areasHelp: string;
  zoneSearch: string;
  zoneSearchPlaceholder: string;
  zoneGroupLabels: Record<string, string>;
  noZoneResults: string;
  moveIn: string;
  moveOut: string;
  notes: string;
  notesPlaceholder: string;
  submit: string;
  loading: string;
  requiredError: string;
  success: string;
  duplicate: string;
  localSave: string;
  legalHeader: string;
  legalOpt1: string;
  legalOpt2: string;
  legalOpt3: string;
  viewPolicy: string;
  sideTitle: string;
  sideText: string;
  sidePoints: string[];
  trustMessage: string;
  statsTitle: string;
  stats: string[];
  areaMapTitle: string;
  areaMapBody: string;
  completionEyebrow: string;
  completionTitle: string;
  completionBody: string;
  completionButton: string;
  districtFallback: string;
  policyContent: string;
  genderOptions: string[];
  livingOptions: string[];
  roomOptions: string[];
}

export const copy: Record<Language, CopySet> = {
  Español: {
    badge: "Madrid roommate matching",
    eyebrow: "HausMate Match",
    headline: "Encuentra tu compañero ideal para vivir en Madrid.",
    intro:
      "Completa tu perfil y te conectamos con roommates compatibles y zonas que encajen contigo.",
    stickyCta: "Seguir",
    formTitle: "Encuentra tu HausMate",
    progressLabel: "Progreso",
    stepOf: "Paso",
    stepNames: ["Perfil básico", "Preferencias", "Disponibilidad y notas"],
    nextStep: "Continuar",
    previousStep: "Volver",
    name: "Nombre completo *",
    namePlaceholder: "Ej: John Doe",
    wa: "WhatsApp (+34) *",
    waPlaceholder: "+34 600 000 000",
    age: "Tu edad",
    gender: "Tu género",
    livingPreference: "Preferencia de convivencia",
    budget: "Presupuesto mensual (€)",
    budgetPlaceholder: "Ej: 850",
    rooms: "¿Cuántas habitaciones buscas?",
    country: "País de origen",
    countryDefault: "ES",
    countryOptions: [
      { value: "ES", label: "España" },
      { value: "MX", label: "México" },
      { value: "AR", label: "Argentina" },
      { value: "CO", label: "Colombia" },
      { value: "CL", label: "Chile" },
      { value: "PE", label: "Perú" },
      { value: "VE", label: "Venezuela" },
      { value: "US", label: "Estados Unidos" },
      { value: "GB", label: "Reino Unido" },
      { value: "FR", label: "Francia" },
      { value: "DE", label: "Alemania" },
      { value: "IT", label: "Italia" },
      { value: "PT", label: "Portugal" },
      { value: "NL", label: "Países Bajos" },
      { value: "BR", label: "Brasil" },
      { value: "OTHER", label: "Otro" },
    ],
    language: "Idioma principal",
    languageOptions: [
      { value: "es", label: "Español" },
      { value: "en", label: "Inglés" },
      { value: "fr", label: "Francés" },
      { value: "de", label: "Alemán" },
      { value: "it", label: "Italiano" },
      { value: "pt", label: "Portugués" },
      { value: "other", label: "Otro" },
    ],
    urgency: "Urgencia de mudanza",
    urgencyOptions: [
      { value: "urgent", label: "Urgente (<1 mes)" },
      { value: "flexible", label: "Flexible" },
      { value: "planning", label: "Planificando" },
    ],
    lifestyle: "Tu estilo de vida",
    lifestyleOptions: ["Tranquilo", "Social", "Estudiante", "Profesional"],
    areas: "Zonas preferidas",
    areasHelp: "Busca y selecciona los distritos que mejor encajen contigo.",
    zoneSearch: "Buscar distrito",
    zoneSearchPlaceholder: "Buscar distrito",
    zoneGroupLabels: {
      central: "Centro",
      north: "Norte",
      east: "Este",
      south: "Sur",
      west: "Oeste",
    },
    noZoneResults: "No encontramos distritos con ese nombre.",
    moveIn: "¿Cuándo entras?",
    moveOut: "¿Hasta cuándo?",
    notes: "Cuéntanos sobre tu estilo de vida",
    notesPlaceholder: "Trabajo, rutina, hobbies, horarios, convivencia ideal...",
    submit: "Encontrar mi HausMate",
    loading: "Procesando registro...",
    requiredError:
      "Requerido: nombre, WhatsApp y aceptación de las casillas legales.",
    success: "Datos guardados con éxito.",
    duplicate: "Ya recibimos tu solicitud hoy.",
    localSave:
      "Hemos guardado tu perfil para revisión. Si no recibes respuesta pronto, vuelve a intentarlo.",
    legalHeader: "Privacidad y consentimiento",
    legalOpt1: "Acepto la Política de Privacidad. *",
    legalOpt2: "Autorizo compartir mi perfil con otros matches. *",
    legalOpt3: "Acepto contacto por WhatsApp. *",
    viewPolicy: "Ver Política Completa",
    sideTitle: "Un perfil claro para encontrar mejores matches.",
    sideText:
      "Completa tu perfil para encontrar roommates compatibles en Madrid.",
    sidePoints: [
      "Perfil guiado paso a paso",
      "Búsqueda flexible por distritos en Madrid",
      "Contacto por WhatsApp con matches compatibles",
    ],
    trustMessage:
      "Tu información es privada y solo se comparte con matches compatibles.",
    statsTitle: "Confianza HausMate",
    stats: ["+120 matches realizados", "Verificación manual", "Privacidad protegida"],
    areaMapTitle: "Mapa interactivo de zonas",
    areaMapBody:
      "Selecciona distritos desde las etiquetas o directamente en el mapa.",
    completionEyebrow: "Solicitud enviada",
    completionTitle: "Todo listo. Ya recibimos tu perfil.",
    completionBody:
      "Revisaremos tu información y te contactaremos por WhatsApp cuando encontremos matches compatibles.",
    completionButton: "Enviar otro perfil",
    districtFallback: "Sin especificar",
    policyContent: `POLÍTICA DE PRIVACIDAD, CONSENTIMIENTO EXPRESO Y AUTORIZACIÓN DE CESIÓN DE DATOS

Responsable del tratamiento:
HausMate
Email de contacto: info@haus-es.com

Normativa aplicable:
Este tratamiento de datos se realiza en cumplimiento de:

• Reglamento (UE) 2016/679 (Reglamento General de Protección de Datos — RGPD)
• Ley Orgánica 3/2018 de Protección de Datos Personales y Garantía de los Derechos Digitales (LOPDGDD)
• Ley 34/2002 de Servicios de la Sociedad de la Información (LSSI-CE), cuando aplique

1. Datos personales recopilados

Al completar este formulario, el usuario proporciona voluntaria y expresamente los siguientes datos personales:

• Nombre completo
• Número de teléfono y WhatsApp
• Edad
• Género
• País de origen
• Idioma
• Preferencias de convivencia
• Preferencias de ubicación
• Presupuesto
• Fechas de entrada y salida
• Información personal incluida en la descripción del perfil
• Cualquier otra información facilitada voluntariamente

2. Finalidad del tratamiento

El usuario autoriza expresamente a HausMate a tratar sus datos personales con las siguientes finalidades:

• Crear su perfil dentro de la plataforma HausMate
• Analizar compatibilidad con otros usuarios
• Realizar procesos de matching entre usuarios compatibles
• Contactar al usuario mediante WhatsApp, teléfono o medios electrónicos
• Compartir su perfil con otros usuarios potencialmente compatibles
• Facilitar el contacto directo entre usuarios compatibles
• Mejorar el servicio y optimizar los algoritmos de matching

3. Cesión y comunicación de datos a terceros usuarios

El usuario autoriza de forma expresa, informada, específica e inequívoca que HausMate pueda compartir sus datos personales con otros usuarios registrados que sean identificados como potencialmente compatibles.

Esta información puede incluir:

• Nombre
• Edad
• Preferencias
• Descripción personal
• Número de WhatsApp o teléfono
• Información del perfil

La finalidad exclusiva de esta cesión es facilitar el contacto entre usuarios compatibles.

HausMate no venderá los datos a terceros externos.

4. Base jurídica del tratamiento

La base legal del tratamiento es el consentimiento explícito del usuario conforme al artículo 6.1.a del RGPD.

Este consentimiento se otorga mediante la aceptación activa de las casillas correspondientes.

El consentimiento puede retirarse en cualquier momento.

5. Conservación de los datos

Los datos serán conservados durante un máximo de 24 meses desde su registro, salvo que el usuario solicite su eliminación antes.

6. Transferencias internacionales

HausMate utiliza Supabase como proveedor tecnológico, el cual actúa como Encargado del Tratamiento conforme al artículo 28 del Reglamento (UE) 2016/679 (RGPD). Los datos se almacenan en servidores seguros ubicados dentro de la Unión Europea (Irlanda), garantizando el cumplimiento de la normativa europea de protección de datos.

7. Derechos del usuario

El usuario puede ejercer en cualquier momento sus derechos de:

• Acceso
• Rectificación
• Supresión (derecho al olvido)
• Limitación del tratamiento
• Oposición
• Portabilidad

Enviando una solicitud a:

info@haus-es.com

8. Consentimiento explícito y aceptación

Al aceptar las casillas correspondientes, el usuario declara que:

• Ha leído y comprendido esta política
• Autoriza expresamente el tratamiento de sus datos
• Autoriza el contacto vía WhatsApp, teléfono o medios electrónicos
• Autoriza la cesión de sus datos a otros usuarios compatibles
• Comprende que el objetivo es facilitar procesos de matching

Este consentimiento constituye una base legal válida conforme al RGPD.

Fecha de última actualización: 2026`,
    genderOptions: ["Mujer", "Hombre", "Otro"],
    livingOptions: ["Mixto", "Solo Mujeres", "Solo Hombres"],
    roomOptions: ["1", "2", "3", "4", "5+"],
  },
  English: {
    badge: "Madrid roommate matching",
    eyebrow: "HausMate Match",
    headline: "Find the right roommate for your life in Madrid.",
    intro:
      "Complete your profile and we will connect you with compatible roommates and neighborhoods.",
    stickyCta: "Continue",
    formTitle: "Find your HausMate",
    progressLabel: "Progress",
    stepOf: "Step",
    stepNames: ["Basic profile", "Preferences", "Availability & notes"],
    nextStep: "Continue",
    previousStep: "Back",
    name: "Full Name *",
    namePlaceholder: "Ex: John Doe",
    wa: "WhatsApp (with +) *",
    waPlaceholder: "+34 600 000 000",
    age: "Your age",
    gender: "Your gender",
    livingPreference: "Living preference",
    budget: "Monthly budget (€)",
    budgetPlaceholder: "Ex: 850",
    rooms: "How many rooms are you looking for?",
    country: "Country of origin",
    countryDefault: "ES",
    countryOptions: [
      { value: "ES", label: "Spain" },
      { value: "MX", label: "Mexico" },
      { value: "AR", label: "Argentina" },
      { value: "CO", label: "Colombia" },
      { value: "CL", label: "Chile" },
      { value: "PE", label: "Peru" },
      { value: "VE", label: "Venezuela" },
      { value: "US", label: "United States" },
      { value: "GB", label: "United Kingdom" },
      { value: "FR", label: "France" },
      { value: "DE", label: "Germany" },
      { value: "IT", label: "Italy" },
      { value: "PT", label: "Portugal" },
      { value: "NL", label: "Netherlands" },
      { value: "BR", label: "Brazil" },
      { value: "OTHER", label: "Other" },
    ],
    language: "Main language",
    languageOptions: [
      { value: "es", label: "Spanish" },
      { value: "en", label: "English" },
      { value: "fr", label: "French" },
      { value: "de", label: "German" },
      { value: "it", label: "Italian" },
      { value: "pt", label: "Portuguese" },
      { value: "other", label: "Other" },
    ],
    urgency: "Move-in urgency",
    urgencyOptions: [
      { value: "urgent", label: "Urgent (<1 month)" },
      { value: "flexible", label: "Flexible" },
      { value: "planning", label: "Planning ahead" },
    ],
    lifestyle: "Your lifestyle",
    lifestyleOptions: ["Quiet", "Social", "Student", "Professional"],
    areas: "Preferred areas",
    areasHelp: "Search and select the districts that best fit you.",
    zoneSearch: "Search district",
    zoneSearchPlaceholder: "Search district",
    zoneGroupLabels: {
      central: "Central",
      north: "North",
      east: "East",
      south: "South",
      west: "West",
    },
    noZoneResults: "No districts matched that search.",
    moveIn: "Move-in date",
    moveOut: "Move-out date",
    notes: "Tell us about your lifestyle",
    notesPlaceholder: "Work, routine, hobbies, schedule, ideal living dynamic...",
    submit: "Start Matching",
    loading: "Processing registration...",
    requiredError: "Required: name, WhatsApp, and all legal checkboxes.",
    success: "Data saved successfully.",
    duplicate: "We already received your request today.",
    localSave:
      "We saved your profile for review. If you do not hear from us soon, please try again.",
    legalHeader: "Privacy and consent",
    legalOpt1: "I accept the Privacy Policy. *",
    legalOpt2: "I authorize sharing my profile with matches. *",
    legalOpt3: "I agree to be contacted via WhatsApp. *",
    viewPolicy: "View Full Policy",
    sideTitle: "A clearer profile leads to better roommate matches.",
    sideText:
      "Complete your profile to find compatible roommates in Madrid.",
    sidePoints: [
      "Guided step-by-step profile flow",
      "Flexible district search across Madrid",
      "WhatsApp-ready contact with compatible matches",
    ],
    trustMessage:
      "Your information stays private and is only shared with compatible matches.",
    statsTitle: "Why users trust HausMate",
    stats: ["120+ matches completed", "Manual review", "Protected privacy"],
    areaMapTitle: "Interactive area map",
    areaMapBody:
      "Select districts from the tags or directly on the map.",
    completionEyebrow: "Profile sent",
    completionTitle: "You are all set. We received your profile.",
    completionBody:
      "We will review your information and contact you on WhatsApp when we find compatible matches.",
    completionButton: "Submit another profile",
    districtFallback: "Not specified",
    policyContent: `PRIVACY POLICY, EXPLICIT CONSENT AND DATA SHARING AUTHORIZATION

Data Controller:
HausMate
Contact email: info@haus-es.com

Applicable regulations:

This data processing complies with:

• Regulation (EU) 2016/679 (General Data Protection Regulation — GDPR)
• Spanish Organic Law 3/2018 on Data Protection (LOPDGDD)
• Information Society Services Law (LSSI-CE), when applicable

1. Personal data collected

By completing this form, the user voluntarily and explicitly provides the following personal data:

• Full name
• Phone number and WhatsApp
• Age
• Gender
• Country of origin
• Language
• Living preferences
• Location preferences
• Budget
• Move-in and move-out dates
• Personal description
• Any additional voluntarily provided information

2. Purpose of processing

The user explicitly authorizes HausMate to process their data for the following purposes:

• Creating their HausMate profile
• Performing compatibility analysis
• Matching users with compatible roommates
• Contacting the user via WhatsApp, phone, or electronic means
• Sharing their profile with potentially compatible users
• Facilitating direct communication between users
• Improving the matching service

3. Data sharing with other users

The user expressly authorizes HausMate to share their personal data with other registered users when compatibility is identified.

This may include:

• Name
• Age
• Preferences
• Profile description
• WhatsApp or phone number
• Profile information

This sharing is strictly limited to roommate matching purposes.

HausMate does not sell personal data to external third parties.

4. Legal basis

The legal basis for processing is the user's explicit consent under Article 6.1.a of the GDPR.

Consent is granted by actively selecting the required checkboxes.

Consent may be withdrawn at any time.

5. Data retention

Data will be stored for a maximum period of 24 months unless deletion is requested earlier.

6. International transfers

HausMate uses Supabase as a technology provider, acting as a Data Processor under Article 28 GDPR. Data is stored on secure servers located within the European Union (Ireland), ensuring compliance with EU data protection laws.

7. User rights

Users may exercise their rights of:

• Access
• Rectification
• Erasure
• Restriction
• Objection
• Portability

by contacting:

info@haus-es.com

8. Explicit consent and acceptance

By accepting the required checkboxes, the user confirms that they:

• Have read and understood this policy
• Explicitly consent to the processing of their personal data
• Authorize contact via WhatsApp, phone, or electronic means
• Authorize the sharing of their data with compatible users
• Understand the purpose is to facilitate roommate matching

This consent constitutes a valid legal basis under GDPR.

Last updated: 2026`,
    genderOptions: ["Woman", "Man", "Other"],
    livingOptions: ["Mixed", "Women only", "Men only"],
    roomOptions: ["1", "2", "3", "4", "5+"],
  },
};
