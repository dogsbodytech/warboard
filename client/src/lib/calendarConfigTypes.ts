export interface CalendarConfig {
    title:     string;
    calendars: ExternalCalendar[];
}

export interface ExternalCalendar {
    credentials: string;
    gid:         string;
    calendarId:  string;
    showDescription?: boolean;
}
