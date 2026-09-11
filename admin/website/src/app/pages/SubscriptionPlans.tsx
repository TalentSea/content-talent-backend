import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Check, Plus, Edit, Trash2, Zap, Tag, Sparkles, Loader2, ChevronLeft, ChevronRight } from "lucide-react";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  getSubscriptionPlans,
  createSubscriptionPlan,
  updateSubscriptionPlan,
  deleteSubscriptionPlan,
  toggleSubscriptionPlanActive,
  reorderSubscriptionPlans,
  ApiSubscriptionPlan,
} from "../services/apiService";

type Plan = {
  id: string;
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

function getMaxPeriodLimit(unit: string): number {
  const u = (unit || "months").toLowerCase();
  if (u.startsWith("day")) return 365;
  if (u.startsWith("year")) return 3;
  return 24; // months
}

function parsePeriod(periodStr: string): { count: number; unit: string } {
  if (!periodStr) return { count: 1, unit: "months" };
  const trimmed = periodStr.trim().toLowerCase();
  const match = trimmed.match(/^(\d+)\s*(.*)$/);
  if (match) {
    let unit = match[2].trim();
    if (unit.startsWith("day")) unit = "days";
    else if (unit.startsWith("year")) unit = "years";
    else unit = "months";

    const maxLimit = getMaxPeriodLimit(unit);
    const rawCount = parseInt(match[1], 10) || 1;
    const count = Math.max(1, Math.min(maxLimit, rawCount));
    return { count, unit };
  } else {
    let unit = "months";
    if (trimmed.includes("day")) unit = "days";
    else if (trimmed.includes("year")) unit = "years";
    return { count: 1, unit };
  }
}

function formatPeriod(count: number, unit: string): string {
  const maxLimit = getMaxPeriodLimit(unit);
  const c = Math.max(1, Math.min(maxLimit, count || 1));
  const u = (unit || "months").toLowerCase();
  let base = "month";
  if (u.startsWith("day")) base = "day";
  else if (u.startsWith("year")) base = "year";
  else base = "month";

  if (c === 1) {
    return base;
  }
  return `${c} ${base}s`;
}

function transformApiPlanToLocalPlan(apiPlan: ApiSubscriptionPlan): Plan {
  return {
    id: String(apiPlan.id),
    name: apiPlan.name,
    price: apiPlan.base_price,
    discount: apiPlan.discount_percentage,
    period: formatPeriod(apiPlan.billing_period_value, apiPlan.billing_period_unit),
    badgeText: apiPlan.badge_text || undefined,
    description: apiPlan.description || "",
    subscribers: apiPlan.active_subscribers || 0,
    revenue: formatRupees(apiPlan.monthly_revenue || 0),
    features: Array.isArray(apiPlan.features) ? apiPlan.features : [],
    active: apiPlan.is_active,
    popular: Boolean(
      apiPlan.badge_text &&
        (apiPlan.badge_text.toLowerCase().includes("popular") || apiPlan.badge_text.toLowerCase().includes("best"))
    ),
  };
}

function ActiveToggleButton({
  active,
  onToggle,
  id,
}: {
  active: boolean;
  onToggle: (newActive: boolean) => void;
  id?: string;
}) {
  return (
    <button
      type="button"
      id={id}
      role="switch"
      aria-checked={active}
      onClick={() => onToggle(!active)}
      className={`relative inline-flex h-8 w-16 items-center rounded-full p-1 transition-all duration-300 ease-in-out cursor-pointer shadow-inner ${
        active
          ? "bg-gradient-to-r from-emerald-400 via-teal-400 to-blue-500 shadow-lg shadow-emerald-500/20"
          : "bg-slate-700/90 border border-slate-600/80"
      }`}
    >
      <span
        className={`inline-block h-6 w-6 rounded-full bg-white shadow-md transform transition-transform duration-300 ease-in-out ${
          active ? "translate-x-8" : "translate-x-0"
        }`}
      />
    </button>
  );
}

function PlanDialog({ open, onClose, onSave, plan }: {
  open: boolean;
  onClose: () => void;
  onSave: (plan: Plan) => void;
  plan?: Plan | null;
}) {
  const isEdit = !!plan;
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [discount, setDiscount] = useState("");
  const [periodCount, setPeriodCount] = useState("1");
  const [periodUnit, setPeriodUnit] = useState("months");
  const [badgeText, setBadgeText] = useState("");
  const [description, setDescription] = useState("");
  const [features, setFeatures] = useState("");
  const [active, setActive] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (plan) {
      setName(plan.name);
      setPrice(String(plan.price));
      setDiscount(plan.discount ? String(plan.discount) : "");
      const parsed = parsePeriod(plan.period);
      setPeriodCount(String(parsed.count));
      setPeriodUnit(parsed.unit);
      setBadgeText(plan.badgeText || "");
      setDescription(plan.description);
      setFeatures(plan.features.join("\n"));
      setActive(plan.active);
    } else {
      setName("");
      setPrice("");
      setDiscount("");
      setPeriodCount("1");
      setPeriodUnit("months");
      setBadgeText("");
      setDescription("");
      setFeatures("");
      setActive(true);
    }
  }, [plan, open]);

  const numPrice = parseFloat(price) || 0;
  const numDiscount = Math.max(0, Math.min(100, parseFloat(discount) || 0));
  const finalPrice = numDiscount > 0 ? numPrice - (numPrice * numDiscount) / 100 : numPrice;
  const maxLimit = getMaxPeriodLimit(periodUnit);
  const numPeriodCount = Math.max(1, Math.min(maxLimit, parseInt(periodCount) || 1));
  const computedPeriod = formatPeriod(numPeriodCount, periodUnit);

  const handleDiscountChange = (val: string) => {
    if (val === "") {
      setDiscount("");
      return;
    }
    const num = parseFloat(val);
    if (isNaN(num)) {
      setDiscount("");
      return;
    }
    if (num > 100) {
      setDiscount("100");
    } else if (num < 0) {
      setDiscount("0");
    } else {
      setDiscount(val);
    }
  };

  const handleUnitChange = (newUnit: string) => {
    setPeriodUnit(newUnit);
    const limit = getMaxPeriodLimit(newUnit);
    const current = parseInt(periodCount) || 1;
    if (current > limit) {
      setPeriodCount(String(limit));
    }
  };

  const handlePeriodCountChange = (val: string) => {
    if (val === "") {
      setPeriodCount("");
      return;
    }
    const num = parseInt(val, 10);
    if (isNaN(num)) {
      setPeriodCount("1");
      return;
    }
    const limit = getMaxPeriodLimit(periodUnit);
    if (num > limit) {
      setPeriodCount(String(limit));
    } else if (num < 1) {
      setPeriodCount("1");
    } else {
      setPeriodCount(String(num));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSubmitting(true);
    const parsedCount = parseInt(periodCount, 10) || 1;
    const computedPeriodStr = formatPeriod(parsedCount, periodUnit);

    const payload = {
      name: name.trim(),
      base_price: numPrice,
      discount_percentage: numDiscount,
      billing_period_value: parsedCount,
      billing_period_unit: periodUnit,
      description: description.trim() || null,
      features: features.split("\n").map((f) => f.trim()).filter(Boolean),
      badge_text: badgeText.trim() || null,
      is_active: active,
    };

    try {
      if (isEdit && plan) {
        const numericId = parseInt(plan.id, 10);
        if (!isNaN(numericId)) {
          const res = await updateSubscriptionPlan(numericId, payload);
          onSave(transformApiPlanToLocalPlan(res));
        } else {
          onSave({
            id: plan.id,
            name: name.trim(),
            price: numPrice,
            discount: numDiscount,
            period: computedPeriodStr,
            badgeText: badgeText.trim(),
            description: description.trim(),
            subscribers: plan.subscribers,
            revenue: plan.revenue,
            features: features.split("\n").map((f) => f.trim()).filter(Boolean),
            active: active,
          });
        }
      } else {
        const res = await createSubscriptionPlan(payload);
        onSave(transformApiPlanToLocalPlan(res));
      }
    } catch (err) {
      console.warn("[PlanDialog] Saving plan to API failed, fallback to local update", err);
      const updated: Plan = {
        id: plan?.id || String(Date.now()),
        name: name.trim(),
        price: numPrice,
        discount: numDiscount,
        period: computedPeriodStr,
        badgeText: badgeText.trim(),
        description: description.trim(),
        subscribers: plan?.subscribers ?? 0,
        revenue: plan?.revenue ?? "₹0",
        features: features.split("\n").map((f) => f.trim()).filter(Boolean),
        active: active,
        popular: plan?.popular,
      };
      onSave(updated);
    } finally {
      setSubmitting(false);
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col p-6 overflow-hidden">
        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <DialogHeader>
            <DialogTitle>{isEdit ? `Edit "${plan!.name}" Plan` : "Create New Subscription Plan"}</DialogTitle>
            <DialogDescription>
              {isEdit ? "Update the plan details below" : "Set up a new pricing tier for your subscribers"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 my-4 overflow-y-auto max-h-[60vh] pr-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="plan-name">Plan Name</Label>
                <Input
                  id="plan-name"
                  placeholder="e.g., Premium"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="plan-price">Base Price (₹)</Label>
                <Input
                  id="plan-price"
                  placeholder="e.g., 999"
                  type="number"
                  min="0"
                  step="any"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="plan-discount">Discount (%)</Label>
                <Input
                  id="plan-discount"
                  placeholder="0"
                  type="number"
                  min="0"
                  max="100"
                  step="any"
                  value={discount}
                  onChange={(e) => handleDiscountChange(e.target.value)}
                />
                <p className="text-xs text-slate-400 mt-1">
                  Max: 100%
                </p>
              </div>
              <div>
                <Label>Billing Period</Label>
                <div className="flex gap-2 mt-1">
                  <div className="w-1/3">
                    <Input
                      id="plan-period-count"
                      type="number"
                      min="1"
                      max={maxLimit}
                      placeholder="1"
                      value={periodCount}
                      onChange={(e) => handlePeriodCountChange(e.target.value)}
                    />
                  </div>
                  <div className="w-2/3">
                    <Select value={periodUnit} onValueChange={handleUnitChange}>
                      <SelectTrigger id="plan-period-unit">
                        <SelectValue placeholder="Select unit" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="days">Days</SelectItem>
                        <SelectItem value="months">Months</SelectItem>
                        <SelectItem value="years">Years</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Max: {maxLimit} {periodUnit}
                </p>
              </div>
            </div>

            {/* Custom Badge Text Input */}
            <div>
              <Label htmlFor="plan-badge">Badge Text (Optional)</Label>
              <Input
                id="plan-badge"
                placeholder="e.g., Most Popular, Best Value, Limited Time Deal"
                value={badgeText}
                onChange={(e) => setBadgeText(e.target.value)}
              />
            </div>

            {/* Calculated Price Preview */}
            <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-3 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-300 flex items-center gap-2">
                <Tag className="h-4 w-4 text-purple-400" /> Calculated Final Price:
              </span>
              <div className="text-right">
                <span className="text-lg font-bold text-emerald-400">
                  {formatRupees(finalPrice)}/{computedPeriod}
                </span>
                {numDiscount > 0 && (
                  <span className="text-xs text-slate-400 block">
                    Original: {formatRupees(numPrice)} ({numDiscount}% OFF)
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between py-2 border-y border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <Label className="text-slate-200 text-sm font-medium">Status:</Label>
                  <span className={`text-xs font-semibold ${active ? "text-emerald-400" : "text-slate-400"}`}>
                    {active ? "Active" : "Inactive"}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">Toggle visibility for users on your website</p>
              </div>
              <ActiveToggleButton active={active} onToggle={setActive} id="plan-active" />
            </div>

            <div>
              <Label htmlFor="plan-description">Description</Label>
              <Textarea
                id="plan-description"
                placeholder="Brief description of this plan"
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="plan-features">Features (one per line)</Label>
              <Textarea
                id="plan-features"
                placeholder={"Access to premium content\n4K video quality\nPriority support"}
                rows={4}
                value={features}
                onChange={(e) => setFeatures(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter className="pt-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting} className="bg-purple-600 hover:bg-purple-500 text-white font-semibold gap-2">
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {isEdit ? "Save Changes" : "Create Plan"}
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
  const [createOpen, setCreateOpen] = useState(false);
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
    setPlans((prev) => {
      const exists = prev.some((p) => p.id === savedPlan.id);
      if (exists) {
        return prev.map((p) => (p.id === savedPlan.id ? savedPlan : p));
      }
      return [...prev, savedPlan];
    });
  };

  const handleDeletePlan = async (id: string) => {
    const numericId = parseInt(id, 10);
    if (!isNaN(numericId)) {
      try {
        await deleteSubscriptionPlan(numericId);
      } catch (err) {
        console.warn("[SubscriptionPlans] Failed to delete plan from API", err);
      }
    }
    setPlans((prev) => prev.filter((p) => p.id !== id));
  };

  const handleToggleActive = async (id: string, active: boolean) => {
    setPlans((prev) => prev.map((p) => (p.id === id ? { ...p, active } : p)));

    const numericId = parseInt(id, 10);
    if (!isNaN(numericId)) {
      try {
        await toggleSubscriptionPlanActive(numericId);
      } catch (err) {
        console.warn("[SubscriptionPlans] Failed to toggle active status on API", err);
      }
    }
  };

  const handleMovePlan = async (index: number, direction: "prev" | "next") => {
    const targetIndex = direction === "prev" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= plans.length) return;

    const newPlans = [...plans];
    const [moved] = newPlans.splice(index, 1);
    newPlans.splice(targetIndex, 0, moved);
    setPlans(newPlans);

    const ids = newPlans.map((p) => parseInt(p.id, 10)).filter((id) => !isNaN(id));
    if (ids.length > 0) {
      try {
        await reorderSubscriptionPlans(ids);
      } catch (err) {
        console.warn("[SubscriptionPlans] Failed to persist plan reordering", err);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Controlled dialogs at top level */}
      <PlanDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSave={handleSavePlan}
      />
      <PlanDialog
        open={!!editPlan}
        onClose={() => setEditPlan(null)}
        onSave={handleSavePlan}
        plan={editPlan}
      />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Subscription Plans</h1>
          <p className="text-slate-300 mt-1 font-medium">Create and manage your subscription tiers</p>
        </div>
        <Button
          className="gap-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold shadow-lg shadow-purple-600/20"
          onClick={() => setCreateOpen(true)}
        >
          <Plus className="h-4 w-4" />Create Plan
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 text-purple-400 animate-spin" />
        </div>
      ) : plans.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 border border-dashed border-slate-800 rounded-xl bg-slate-900/40 text-center p-8">
          <Sparkles className="h-10 w-10 text-purple-400 mb-3" />
          <h3 className="text-lg font-bold text-white">No Subscription Plans Found</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-sm">
            Create your first subscription tier to start offering plans to your subscribers.
          </p>
          <Button
            className="mt-4 gap-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold"
            onClick={() => setCreateOpen(true)}
          >
            <Plus className="h-4 w-4" /> Create First Plan
          </Button>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
        {plans.map((plan, index) => {
          const basePrice = plan.price;
          const discountVal = plan.discount || 0;
          const hasDiscount = discountVal > 0;
          const finalPrice = hasDiscount ? basePrice - (basePrice * discountVal) / 100 : basePrice;

          return (
            <Card
              key={plan.id}
              className={
                plan.popular
                  ? "border-purple-500 border-2 shadow-[0_0_20px_rgba(168,85,247,0.2)] flex flex-col justify-between"
                  : "border-slate-800 flex flex-col justify-between"
              }
            >
              <CardHeader className="border-b border-slate-800/80">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-xl font-bold text-white">{plan.name}</CardTitle>
                      {plan.popular && <Zap className="h-4 w-4 text-purple-400 fill-purple-400" />}
                    </div>
                    <p className="text-sm text-slate-300 mt-1 font-medium">{plan.description}</p>
                  </div>
                  <div className="flex items-center gap-0.5">
                    {index > 0 && (
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Move Left"
                        onClick={() => handleMovePlan(index, "prev")}
                        className="text-slate-400 hover:text-white hover:bg-slate-800 h-8 w-8"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                    )}
                    {index < plans.length - 1 && (
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Move Right"
                        onClick={() => handleMovePlan(index, "next")}
                        className="text-slate-400 hover:text-white hover:bg-slate-800 h-8 w-8"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Edit Plan"
                      onClick={() => setEditPlan(plan)}
                      className="text-slate-300 hover:text-white hover:bg-slate-800 h-8 w-8"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title="Delete Plan"
                      onClick={() => handleDeletePlan(plan.id)}
                      className="text-rose-400 hover:text-rose-300 hover:bg-rose-950/40 h-8 w-8"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="flex items-baseline gap-2 flex-wrap">
                    <span className="text-3xl lg:text-4xl font-bold text-white">
                      {formatRupees(finalPrice)}
                    </span>
                    {hasDiscount && (
                      <span className="text-lg font-medium text-slate-400 line-through">
                        {formatRupees(basePrice)}
                      </span>
                    )}
                    <span className="text-slate-400 text-sm font-medium">/{plan.period}</span>
                    {hasDiscount && (
                      <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2 py-0.5 rounded-full font-semibold">
                        {discountVal}% OFF
                      </span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6 flex flex-col justify-between flex-1">
                <div>
                  <div className="space-y-4 mb-6">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-300 font-medium">Active Subscribers</span>
                      <span className="font-semibold text-white">{plan.subscribers.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-300 font-medium">Monthly Revenue</span>
                      <span className="font-semibold text-emerald-400">{plan.revenue}</span>
                    </div>
                  </div>
                  <div className="space-y-3 mb-6">
                    <div className="font-semibold text-sm text-white">Features:</div>
                    {plan.features.map((feature, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-sm">
                        <Check className="h-4 w-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-200 font-normal">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Footer section: Badge Text directly above Active/Inactive toggle button */}
                <div className="pt-4 border-t border-slate-800/80 space-y-3 mt-auto">
                  {plan.badgeText && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400 font-medium">Badge Tag:</span>
                      <span className="inline-flex items-center gap-1.5 bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs px-2.5 py-0.5 rounded-full font-medium">
                        <Sparkles className="h-3 w-3 text-purple-400" />
                        {plan.badgeText}
                      </span>
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-400 font-medium">Status:</span>
                      <span className={`text-xs font-semibold ${plan.active ? "text-emerald-400" : "text-slate-400"}`}>
                        {plan.active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <ActiveToggleButton
                      active={plan.active}
                      onToggle={(checked) => handleToggleActive(plan.id, checked)}
                      id={`plan-${plan.id}`}
                    />
                  </div>
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
