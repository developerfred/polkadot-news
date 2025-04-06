import React, { ReactNode } from "react";
import { Observable } from "rxjs";
import { StateObservable } from "@rx-state/core";
export declare const useSubscription: () => ((src: StateObservable<any>) => void) | null;
/**
 * A React Component that:
 * - collects the subscriptions of its children and it unsubscribes them when
 * the component unmounts.
 * - if a source$ property is used, then it ensures that the subscription to the
 * observable will exist before the children gets rendered, and it unsubscribes
 * from it when the component unmounts.
 *
 * If the fallback property is used, then the component will create a Suspense
 * boundary with the provided JSX Element, otherwise it will render null until
 * the subscription exists.
 *
 * @param [source$] (=undefined) - Source observable that the Component will
 * subscrib to before it renders its children.
 * @param [fallback] (=null) - JSX Element to be used by the Suspense boundary.
 *
 * @remarks This Component doesn't trigger any updates from the source$.
 */
export declare const Subscribe: React.FC<{
    children?: React.ReactNode | undefined;
    source$?: Observable<any>;
    fallback?: NonNullable<ReactNode> | null;
}>;
/**
 * Component that prevents its children from using the parent `Subscribe` boundary
 * to manage their subscriptions.
 */
export declare const RemoveSubscribe: React.FC<{
    children?: React.ReactNode | undefined;
}>;
