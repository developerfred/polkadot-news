import { state as coreState } from "@rx-state/core";
import { ReactElement } from "react";
declare module "@rx-state/core" {
    interface StateObservable<T> extends ReactElement {
    }
}
export declare const state: typeof coreState;
