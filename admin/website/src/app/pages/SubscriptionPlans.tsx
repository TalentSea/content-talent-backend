import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import {
  Check, Edit, Zap, Tag, Sparkles, Loader2, Lock, Users, DollarSign, ShieldCheck,
} from "lucide-react";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import {
  getSubscriptionPlans,
  updateSubscriptionPlan,
  ApiSubscriptionPlan,
} from "../services/apiService";

export type Plan = {
  id: string;
  planType: string;
  name: string;
  price: number;
  discount: number;
  period: string;
  badgeText?: string;
  description: string;
  subscribers: number;
  revenue: string;
  features: string[];
  active: boolean;
  popular?: boolean;
};

const formatRupees = (val: number) => {
  const formatted = val % 1 === 0 ? val.toLocaleString("en-IN") : val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return `₹${formatted}`;
};

function transformApiPlanToLocalPlan(apiPlan: ApiSubscriptionPlan): Plan {
  const planType = apiPlan.plan_type || (apiPlan.display_order === 2 ? "no_ads" : "with_ads");
  return {
    id: String(apiPlan.id),
    planType,
    name: apiPlan.name,
    price: apiPlan.base_price,
    discount: apiPlan.discount_percentage,
    period: "month",
    badgeText: apiPlan.badge_text || undefined,
    description: apiPlan.description || "",
    subscribers: apiPlan.active_subscribers || 0,
    revenue: formatRupees(apiPlan.monthly_revenue || 0),
    features: Array.isArray(apiPlan.features) ? apiPlan.features : [],
    active: apiPlan.is_active,
    popular: Boolean(
      planType === "no_ads" ||
        (apiPlan.badge_text &&
          (apiPlan.badge_text.toLowerCase().includes("popular") ||
            apiPlan.badge_text.toLowerCase().includes("best") ||
            apiPlan.badge_text.toLowerCase().includes("deal")))
    ),
  };
}

function EditPlanDialog({
  open,
  onClose,
  onSave,
  plan,
}: {
  open: boolean;
  onClose: () => void;
  onSave: (plan: Plan) => void;
  plan?: Plan | null;
}) {
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [discount, setDiscount] = useState("");
  const [badgeText, setBadgeText] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (plan) {
      setName(plan.name);
      setPrice(String(plan.price));
      setDiscount(plan.discount > 0 ? String(plan.discount) : "");
      setBadgeText(plan.badgeText || "");
      setDescription(plan.description || "");
      setError(null);
    }
  }, [plan, open]);

  if (!plan) return null;

  const numPrice = parseFloat(price) || 0;
  const numDiscount = Math.min(100, Math.max(0, parseFloat(discount) || 0));
  const finalPrice = numDiscount > 0 ? numPrice - (numPrice * numDiscount) / 100 : numPrice;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Plan name is required");
      return;
    }

    setSubmitting(true);
    setError(null);

    const payload = {
      name: name.trim(),
      description: description.trim() || null,
      base_price: numPrice,
      discount_percentage: numDiscount,
      badge_text: badgeText.trim() || null,
    };

    try {
      const numericId = parseInt(plan.id, 10);
      const res = await updateSubscriptionPlan(numericId, payload);
      onSave(transformApiPlanToLocalPlan(res));
      toast.success(`Subscription plan "${res.name}" updated successfully.`);
      onClose();
    } catch (err: any) {
      console.error("[SubscriptionPlans] Update failed:", err);
      const msg = err?.message || "Failed to update subscription plan pricing.";
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const isNoAds = plan.planType === "no_ads";

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-xl max-h-[90vh] flex flex-col p-6 overflow-hidden bg-white border border-slate-200 text-slate-900 rounded-2xl shadow-2xl">
        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <DialogHeader>
            <div className="flex items-center gap-2 mb-1">
              <Badge
                variant="outline"
                className="border-slate-200 bg-slate-100 text-slate-700 font-mono text-[10px] font-semibold uppercase"
              >
                {isNoAds ? "TIER 2: PREMIUM AD-FREE" : "TIER 1: STANDARD WITH ADS"}
              </Badge>
            </div>
            <DialogTitle className="text-xl font-bold text-slate-900">
              Edit "{plan.name}" Pricing
            </DialogTitle>
            <DialogDescription className="text-slate-500 text-sm mt-1">
              Update plan pricing, discounts, and highlights.
            </DialogDescription>
          </DialogHeader>

          {error && (
            <div className="mt-3 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {error}
            </div>
          )}

          <div className="space-y-4 my-4 overflow-y-auto max-h-[55vh] pr-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="plan-name" className="text-sm font-semibold text-slate-800 block mb-1.5">
                  Plan Display Name
                </Label>
                <Input
                  id="plan-name"
                  placeholder="e.g. Standard or Premium"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="bg-white border-slate-200 text-slate-900 focus:border-slate-900 focus:ring-1 focus:ring-slate-900 rounded-xl shadow-xs"
                  required
                />
              </div>
              <div>
                <Label htmlFor="plan-price" className="text-sm font-semibold text-slate-800 block mb-1.5">
                  Base Price (₹ INR)
                </Label>
                <Input
                  id="plan-price"
                  type="number"
                  min="0"
                  step="any"
                  placeholder="e.g. 499"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  className="bg-white border-slate-200 text-slate-900 focus:border-slate-900 focus:ring-1 focus:ring-slate-900 rounded-xl shadow-xs"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="plan-discount" className="text-sm font-semibold text-slate-800 block mb-1.5">
                  Discount Percentage (%)
                </Label>
                <Input
                  id="plan-discount"
                  type="number"
                  min="0"
                  max="100"
                  step="any"
                  placeholder="0"
                  value={discount}
                  onChange={(e) => setDiscount(e.target.value)}
                  className="bg-white border-slate-200 text-slate-900 focus:border-slate-900 focus:ring-1 focus:ring-slate-900 rounded-xl shadow-xs"
                />
              </div>
              <div>
                <Label htmlFor="plan-badge" className="text-sm font-semibold text-slate-800 block mb-1.5">
                  Marketing Badge (Optional)
                </Label>
                <Input
                  id="plan-badge"
                  placeholder="e.g. POPULAR, BEST VALUE"
                  value={badgeText}
                  onChange={(e) => setBadgeText(e.target.value)}
                  className="bg-white border-slate-200 text-slate-900 focus:border-slate-900 focus:ring-1 focus:ring-slate-900 rounded-xl shadow-xs"
                />
              </div>
            </div>

            {/* Calculated Final Price Callout */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 flex items-center justify-between">
              <span className="text-xs font-medium text-slate-600 flex items-center gap-1.5">
                <Tag className="h-3.5 w-3.5 text-slate-500" />
                Subscriber Charged Price:
              </span>
              <div className="text-right">
                <span className="text-base font-bold text-slate-900">
                  {formatRupees(finalPrice)}/month
                </span>
                {numDiscount > 0 && (
                  <span className="text-[11px] text-slate-500 block">
                    Base: {formatRupees(numPrice)} ({numDiscount}% discount)
                  </span>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="plan-description" className="text-sm font-semibold text-slate-800 block mb-1.5">
                Plan Tagline / Description
              </Label>
              <Textarea
                id="plan-description"
                placeholder="Short benefit highlight shown below the plan title"
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="bg-white border-slate-200 text-slate-900 focus:border-slate-900 focus:ring-1 focus:ring-slate-900 rounded-xl text-sm shadow-xs"
              />
            </div>

            {/* Platform-Governed Features (Read-Only) */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5 text-slate-600" />
                  Platform Technical Entitlements
                </span>
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-mono font-medium">
                  Locked by OTT Engine
                </span>
              </div>
              <div className="space-y-1.5 pt-1">
                {plan.features.map((feature, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs text-slate-600">
                    <Check className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter className="pt-3 border-t border-slate-100 gap-2">
            <Button type="button" variant="outline" onClick={onClose} className="border-slate-200 bg-white text-slate-700 hover:bg-slate-50 rounded-xl shadow-xs">
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-xl gap-2 shadow-xs"
            >
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Save Plan Pricing
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function SubscriptionPlans() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [editPlan, setEditPlan] = useState<Plan | null>(null);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const data = await getSubscriptionPlans();
      if (Array.isArray(data)) {
        setPlans(data.map(transformApiPlanToLocalPlan));
      }
    } catch (err) {
      console.warn("[SubscriptionPlans] Failed to load plans from API", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, []);

  const handleSavePlan = (savedPlan: Plan) => {
    setPlans((prev) => prev.map((p) => (p.id === savedPlan.id ? savedPlan : p)));
  };

  return (
    <div className="space-y-8">
      <EditPlanDialog
        open={!!editPlan}
        onClose={() => setEditPlan(null)}
        onSave={handleSavePlan}
        plan={editPlan}
      />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Subscription Plans</h1>
            <span className="text-xs bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-1 rounded-full font-mono font-medium flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-slate-600" />
              TWO-TIER OTT ENGINE
            </span>
          </div>
          <p className="text-slate-500 mt-1.5 text-sm max-w-2xl font-normal">
            Configure pricing, discounts, and promotional badges for your Standard (With Ads) and Premium (Ad-Free) tiers. Technical entitlements and DRM policies are platform-governed.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-400">
          <Loader2 className="h-8 w-8 text-slate-600 animate-spin" />
          <p className="text-sm font-medium text-slate-600">Synchronizing subscription tiers...</p>
        </div>
      ) : plans.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 border border-dashed border-slate-200 rounded-2xl bg-white text-center p-8 shadow-xs">
          <Sparkles className="h-10 w-10 text-slate-400 mb-3" />
          <h3 className="text-base font-bold text-slate-900">Initializing Two-Tier OTT Engine</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm">
            Contact platform administration if your studio's standard tiers are not automatically initialized.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {plans.map((plan) => {
            const isNoAds = plan.planType === "no_ads";
            const basePrice = plan.price;
            const discountVal = plan.discount || 0;
            const hasDiscount = discountVal > 0;
            const finalPrice = hasDiscount ? basePrice - (basePrice * discountVal) / 100 : basePrice;

            return (
              <Card
                key={plan.id}
                className={`relative flex flex-col justify-between overflow-hidden rounded-2xl transition-all duration-200 bg-white shadow-xs ${
                  isNoAds
                    ? "border-2 border-slate-900 shadow-sm"
                    : "border border-slate-200/80"
                }`}
              >
                <CardHeader className="border-b border-slate-100 pb-6 relative z-10">
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <Badge
                      variant="outline"
                      className="border-slate-200 bg-slate-100 text-slate-700 font-mono text-[10px] tracking-wider uppercase font-semibold"
                    >
                      {isNoAds ? "Tier 2 • Ad-Free" : "Tier 1 • With Ads"}
                    </Badge>

                    {plan.badgeText && (
                      <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-800 border border-amber-200 text-[11px] font-semibold px-2.5 py-0.5 rounded-full shadow-2xs">
                        <Zap className="h-3 w-3 fill-amber-500 text-amber-500" />
                        {plan.badgeText}
                      </span>
                    )}
                  </div>

                  <div>
                    <CardTitle className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                      {plan.name}
                    </CardTitle>
                    <p className="text-sm text-slate-500 mt-1 min-h-[38px] line-clamp-2 font-normal">
                      {plan.description || (isNoAds ? "Unlimited ad-free OTT streaming in Full HD" : "Full access to entire video library with occasional short ads")}
                    </p>
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-100 flex items-baseline gap-2.5 flex-wrap">
                    <span className="text-4xl font-extrabold text-slate-900 tracking-tight">
                      {formatRupees(finalPrice)}
                    </span>
                    {hasDiscount && (
                      <span className="text-lg font-medium text-slate-400 line-through">
                        {formatRupees(basePrice)}
                      </span>
                    )}
                    <span className="text-slate-500 text-sm font-normal">/month</span>
                    {hasDiscount && (
                      <span className="bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs px-2 py-0.5 rounded-full font-semibold">
                        {discountVal}% OFF
                      </span>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="pt-6 flex flex-col justify-between flex-1 relative z-10 space-y-6">
                  {/* Live Studio Telemetry Cards */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
                      <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                        <Users className="h-3.5 w-3.5 text-blue-600" />
                        Active Members
                      </div>
                      <div className="text-lg font-bold text-slate-900">
                        {plan.subscribers.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
                      <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                        <DollarSign className="h-3.5 w-3.5 text-emerald-600" />
                        Monthly Revenue
                      </div>
                      <div className="text-lg font-bold text-slate-900">
                        {plan.revenue}
                      </div>
                    </div>
                  </div>

                  {/* Technical Platform Feature Entitlements */}
                  <div className="space-y-3">
                    <div className="text-xs font-semibold text-slate-700 uppercase tracking-wider font-mono flex items-center justify-between">
                      <span>Platform Capabilities</span>
                      <span className="text-emerald-700 text-[10px] font-normal lowercase">enforced</span>
                    </div>
                    <div className="space-y-2.5">
                      {plan.features.map((feature, idx) => (
                        <div key={idx} className="flex items-start gap-2.5 text-sm">
                          <Check className="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" />
                          <span className="text-slate-600 text-xs font-medium leading-relaxed">
                            {feature}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Edit Action */}
                  <div className="pt-4 border-t border-slate-100">
                    <Button
                      onClick={() => setEditPlan(plan)}
                      className={`w-full h-11 font-medium gap-2 rounded-xl transition-all shadow-xs ${
                        isNoAds
                          ? "bg-slate-900 hover:bg-slate-800 text-white"
                          : "bg-white hover:bg-slate-50 text-slate-700 border border-slate-200"
                      }`}
                    >
                      <Edit className="h-4 w-4" />
                      Configure Pricing & Copy
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
