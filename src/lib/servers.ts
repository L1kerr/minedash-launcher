export interface ServerDef {
  id: string;
  tag: string;
  name: string;
  subtitle: string;
  description: string;
  address: string;
  version: string;
}

export const SERVERS: ServerDef[] = [
  {
    id: 'create',
    tag: 'CREATE-СЕРВЕР',
    name: 'MineDash Community',
    subtitle: '— Индустриальная сборка',
    description:
      'Развивайте мастерскую, соединяйте конвейеры, железнодорожные депо и надёжные механизмы Create в единую производственную систему.',
    address: 'mc.minedash.fun',
    version: '1.21.1'
  }
];
