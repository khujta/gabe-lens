import { create } from "zustand";
type StatementState = { rows: string[]; busy: boolean };
type StatementActions = { load(): void };
export type StatementStore = StatementState & StatementActions;   // an INTERSECTION alias — the shape gastify's stores wear
export const useStatementStore = create<StatementStore>()(() => ({ rows: [], busy: false, load() {} }));
