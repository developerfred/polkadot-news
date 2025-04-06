import { StateObservable, SUSPENSE } from "@rx-state/core";
export declare const useStateObservable: <O>(source$: StateObservable<O>) => Exclude<O, typeof SUSPENSE>;
