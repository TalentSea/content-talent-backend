import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { User, Lock, Bell, CreditCard, Globe, Shield, Save, Loader2, Upload, Check } from "lucide-react";
import { Badge } from "../components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import { Separator } from "../components/ui/separator";
import { getCreatorProfile, updateCreatorProfile, uploadAvatarPhoto, ApiProfile } from "../services/apiService";

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [savingSection, setSavingSection] = useState<string | null>(null);
  const [savedSection, setSavedSection] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form Fields
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [bio, setBio] = useState("");
  const [website, setWebsite] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [twitter, setTwitter] = useState("");
  const [youtube, setYoutube] = useState("");
  const [instagram, setInstagram] = useState("");

  // Load Profile from API
  useEffect(() => {
    setLoading(true);
    getCreatorProfile()
      .then((profile: ApiProfile) => {
        if (profile.firstName) setFirstName(profile.firstName);
        if (profile.lastName) setLastName(profile.lastName);
        if (profile.email) setEmail(profile.email);
        if (profile.bio !== undefined) setBio(profile.bio);
        if (profile.website !== undefined) setWebsite(profile.website);
        if (profile.phone !== undefined) setPhone(profile.phone);
        if (profile.location !== undefined) setLocation(profile.location);
        if (profile.avatarUrl) setAvatarUrl(profile.avatarUrl);
        if (profile.socialLinks) {
          setTwitter(profile.socialLinks.twitter || "");
          setYoutube(profile.socialLinks.youtube || "");
          setInstagram(profile.socialLinks.instagram || "");
        }
      })
      .catch((err) => {
        console.warn("Failed to load creator profile from API", err);
      })
      .finally(() => setLoading(false));
  }, []);

  // Save Section Changes Handler
  const handleSaveSection = async (sectionKey: string) => {
    setSavingSection(sectionKey);
    try {
      if (sectionKey === "profile" || sectionKey === "social") {
        await updateCreatorProfile({
          first_name: firstName,
          last_name: lastName,
          bio,
          website,
          phone,
          location,
          social_links: {
            twitter,
            youtube,
            instagram,
          },
        });
      } else {
        // Minor async delay for other setting section triggers
        await new Promise((resolve) => setTimeout(resolve, 300));
      }
      setSavedSection(sectionKey);
      setTimeout(() => {
        setSavedSection((prev) => (prev === sectionKey ? null : prev));
      }, 3000);
    } catch (err) {
      console.error(`Failed to update ${sectionKey} settings`, err);
    } finally {
      setSavingSection(null);
    }
  };

  // Helper renderer for modular Section Save Buttons
  const renderSaveButton = (sectionKey: string, customLabel = "Save Changes") => {
    const isSaving = savingSection === sectionKey;
    const isSaved = savedSection === sectionKey;

    return (
      <Button
        onClick={() => handleSaveSection(sectionKey)}
        disabled={isSaving || loading}
        size="sm"
        className={`gap-1.5 font-semibold text-xs transition-all duration-200 ${
          isSaved
            ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20"
            : "bg-purple-600 hover:bg-purple-500 text-white shadow-purple-600/20 dark:bg-purple-600 dark:hover:bg-purple-500"
        }`}
      >
        {isSaving ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : isSaved ? (
          <Check className="h-3.5 w-3.5" />
        ) : (
          <Save className="h-3.5 w-3.5" />
        )}
        {isSaving ? "Saving..." : isSaved ? "Saved!" : customLabel}
      </Button>
    );
  };

  // Upload Avatar File
  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    setUploadingAvatar(true);
    try {
      const res = await uploadAvatarPhoto(file);
      if (res.avatarUrl) {
        setAvatarUrl(res.avatarUrl);
      }
    } catch (err) {
      console.error("Failed to upload avatar photo", err);
    } finally {
      setUploadingAvatar(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Hidden File Input for Avatar */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleAvatarChange}
        accept="image/png, image/jpeg, image/webp"
        className="hidden"
      />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-gray-600 mt-1">Manage your account and platform settings</p>
        </div>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-6 lg:w-auto lg:inline-grid">
          <TabsTrigger value="profile" className="gap-2">
            <User className="h-4 w-4" />
            <span className="hidden md:inline">Profile</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2">
            <Lock className="h-4 w-4" />
            <span className="hidden md:inline">Security</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="h-4 w-4" />
            <span className="hidden md:inline">Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-2">
            <CreditCard className="h-4 w-4" />
            <span className="hidden md:inline">Billing</span>
          </TabsTrigger>
          <TabsTrigger value="preferences" className="gap-2">
            <Globe className="h-4 w-4" />
            <span className="hidden md:inline">Preferences</span>
          </TabsTrigger>
          <TabsTrigger value="advanced" className="gap-2">
            <Shield className="h-4 w-4" />
            <span className="hidden md:inline">Advanced</span>
          </TabsTrigger>
        </TabsList>

        {/* Profile Settings */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <CardTitle>Profile Information</CardTitle>
              {renderSaveButton("profile")}
            </CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <div className="flex items-center justify-center py-8 text-slate-400 gap-2">
                  <Loader2 className="h-5 w-5 animate-spin" /> Loading profile details...
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-6">
                    <div className="h-20 w-20 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white text-2xl font-bold overflow-hidden relative">
                      {avatarUrl ? (
                        <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                      ) : (
                        `${firstName.charAt(0)}${lastName.charAt(0)}`
                      )}
                    </div>
                    <div>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={uploadingAvatar}
                        onClick={() => fileInputRef.current?.click()}
                        className="gap-2"
                      >
                        {uploadingAvatar ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
                        {uploadingAvatar ? "Uploading..." : "Change Avatar"}
                      </Button>
                      <p className="text-xs text-gray-500 mt-1">JPG, PNG or WEBP. Max size 2MB</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label htmlFor="first-name">First Name</Label>
                      <Input id="first-name" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
                    </div>
                    <div>
                      <Label htmlFor="last-name">Last Name</Label>
                      <Input id="last-name" value={lastName} onChange={(e) => setLastName(e.target.value)} />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="email">Email Address <span className="text-xs text-slate-400 font-normal">(Read-only)</span></Label>
                    <Input id="email" type="email" value={email} disabled className="bg-slate-100 dark:bg-slate-800 cursor-not-allowed" />
                  </div>
                  <div>
                    <Label htmlFor="bio">Bio</Label>
                    <Input id="bio" value={bio} onChange={(e) => setBio(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="website">Website</Label>
                    <Input id="website" value={website} onChange={(e) => setWebsite(e.target.value)} />
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label htmlFor="phone">Phone Number</Label>
                      <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
                    </div>
                    <div>
                      <Label htmlFor="location">Location</Label>
                      <Input id="location" value={location} onChange={(e) => setLocation(e.target.value)} />
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <CardTitle>Social Links</CardTitle>
              {renderSaveButton("social")}
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="twitter">Twitter</Label>
                <Input id="twitter" value={twitter} onChange={(e) => setTwitter(e.target.value)} placeholder="https://twitter.com/username" />
              </div>
              <div>
                <Label htmlFor="youtube">YouTube</Label>
                <Input id="youtube" value={youtube} onChange={(e) => setYoutube(e.target.value)} placeholder="https://youtube.com/@username" />
              </div>
              <div>
                <Label htmlFor="instagram">Instagram</Label>
                <Input id="instagram" value={instagram} onChange={(e) => setInstagram(e.target.value)} placeholder="https://instagram.com/username" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <CardTitle>Change Password</CardTitle>
              {renderSaveButton("password", "Update Password")}
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="current-password">Current Password</Label>
                <Input id="current-password" type="password" />
              </div>
              <div>
                <Label htmlFor="new-password">New Password</Label>
                <Input id="new-password" type="password" />
              </div>
              <div>
                <Label htmlFor="confirm-password">Confirm New Password</Label>
                <Input id="confirm-password" type="password" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <CardTitle>Two-Factor Authentication</CardTitle>
              {renderSaveButton("2fa")}
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Enable 2FA</div>
                  <div className="text-sm text-gray-600">
                    Add an extra layer of security to your account
                  </div>
                </div>
                <Switch />
              </div>
              <Separator />
              <Button variant="outline">Configure Authenticator App</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notification Settings */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <CardTitle>Email Notifications</CardTitle>
              {renderSaveButton("notifications")}
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">New Subscribers</div>
                  <div className="text-sm text-gray-600">Get notified when someone subscribes</div>
                </div>
                <Switch defaultChecked />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Comments</div>
                  <div className="text-sm text-gray-600">Get notified about new comments</div>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Billing Settings */}
        <TabsContent value="billing" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <CardTitle>Payment Method</CardTitle>
              {renderSaveButton("billing")}
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border border-gray-200 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-16 bg-gradient-to-br from-purple-600 to-blue-600 rounded flex items-center justify-center text-white font-bold">
                    VISA
                  </div>
                  <div>
                    <div className="font-medium">•••• •••• •••• 4242</div>
                    <div className="text-sm text-gray-600">Expires 12/24</div>
                  </div>
                </div>
                <Button variant="outline" size="sm">Edit</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preferences */}
        <TabsContent value="preferences" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <CardTitle>General Preferences</CardTitle>
              {renderSaveButton("preferences")}
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="language">Language</Label>
                <Select defaultValue="en">
                  <SelectTrigger id="language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="es">Spanish</SelectItem>
                    <SelectItem value="fr">French</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Settings */}
        <TabsContent value="advanced" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <CardTitle>Data & Privacy</CardTitle>
              {renderSaveButton("privacy")}
            </CardHeader>
            <CardContent className="space-y-4">
              <Button variant="outline">Download My Data</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
