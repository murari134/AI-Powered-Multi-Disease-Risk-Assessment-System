'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  AlertCircle,
  Building2,
  ExternalLink,
  Filter,
  Globe,
  Loader2,
  MapPin,
  Navigation,
  Phone,
  Search,
  ShieldCheck,
  Stethoscope,
} from 'lucide-react';
import { apiRequest } from '@/lib/api';

interface Hospital {
  id: string;
  name: string;
  city: string;
  country: string;
  address: string;
  type: string;
  emergency: boolean;
  phone: string;
  specialties: string[];
  lat: number;
  lon: number;
  website?: string;
}

export default function HospitalsPage() {
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [specialty, setSpecialty] = useState('');
  const [geoLoading, setGeoLoading] = useState(false);

  const fetchHospitals = async (searchQuery = '', searchSpecialty = '', coords?: { lat: number; lon: number }) => {
    setLoading(true);
    try {
      let url = '/api/v1/hospitals/search?';
      const params = new URLSearchParams();
      if (searchQuery) params.append('query', searchQuery);
      if (searchSpecialty) params.append('specialty', searchSpecialty);
      if (coords) {
        params.append('lat', String(coords.lat));
        params.append('lon', String(coords.lon));
      }

      const res = await apiRequest<{ count: number; results: Hospital[] }>(`${url}${params.toString()}`);
      setHospitals(res.results || []);
    } catch (err) {
      console.error('Failed to search hospitals', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHospitals();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchHospitals(query, specialty);
  };

  const handleUseGeolocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }
    setGeoLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGeoLoading(false);
        fetchHospitals(query, specialty, {
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
        });
      },
      (err) => {
        setGeoLoading(false);
        alert('Could not access location. Please search by city name.');
      },
      { timeout: 8000 }
    );
  };

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Title */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-teal-100 dark:bg-teal-950 text-teal-800 dark:text-teal-300 text-xs font-bold uppercase mb-2">
            Clinical Care Directory
          </div>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white">
            Verified Healthcare Facility Locator
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Search verified tertiary medical centers, specialized cardiology & oncology clinics, and emergency hospitals.
          </p>
        </div>

        <button
          onClick={handleUseGeolocation}
          disabled={geoLoading}
          className="px-4 py-2.5 rounded-xl font-bold text-xs bg-slate-900 text-white dark:bg-white dark:text-slate-950 flex items-center gap-2 shadow-sm self-start sm:self-auto hover:scale-105 transition-all disabled:opacity-50"
        >
          {geoLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Navigation className="w-4 h-4" />}
          <span>Near My Location</span>
        </button>
      </div>

      {/* Search & Filter Form */}
      <form
        onSubmit={handleSearch}
        className="p-4 sm:p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-center gap-3"
      >
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by city, hospital name, or country e.g. Boston, London, AIIMS..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500/40"
          />
        </div>

        <select
          value={specialty}
          onChange={(e) => setSpecialty(e.target.value)}
          className="w-full sm:w-56 px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-xs sm:text-sm font-semibold text-slate-700 dark:text-slate-300"
        >
          <option value="">All Clinical Specialties</option>
          <option value="Cardiology">Cardiology / Heart</option>
          <option value="Oncology">Oncology / Cancer</option>
          <option value="Neurology">Neurology / Stroke</option>
          <option value="Endocrinology">Endocrinology / Diabetes</option>
          <option value="Nephrology">Nephrology / Kidney</option>
          <option value="Pulmonology">Pulmonology / Asthma</option>
        </select>

        <button
          type="submit"
          className="w-full sm:w-auto px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm text-white bg-teal-600 hover:bg-teal-700 transition-colors shadow-sm shrink-0"
        >
          Search Facilities
        </button>
      </form>

      {/* Facilities Cards Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Verified Medical Facilities ({hospitals.length} Found)
          </p>
          <span className="text-[11px] text-slate-400">Data verified via official registries & OpenStreetMap</span>
        </div>

        {loading ? (
          <div className="py-20 text-center flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
            <p className="text-xs text-slate-400">Searching verified medical centers...</p>
          </div>
        ) : hospitals.length === 0 ? (
          <div className="py-20 text-center bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 space-y-3 p-8">
            <Building2 className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto" />
            <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">No facilities matching criteria</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Try broadening your search query or clear the specialty filter to view major global and regional hospitals.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {hospitals.map((h) => (
              <div
                key={h.id}
                className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md hover:border-teal-500/60 transition-all flex flex-col justify-between space-y-4"
              >
                <div>
                  {/* Top info */}
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                        {h.type}
                      </span>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-1.5">
                        {h.name}
                      </h3>
                    </div>

                    {h.emergency && (
                      <span className="shrink-0 text-[10px] font-black uppercase px-2.5 py-1 rounded-full bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300">
                        24/7 Emergency
                      </span>
                    )}
                  </div>

                  {/* Address & City */}
                  <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400 mt-3">
                    <div className="flex items-start gap-2">
                      <MapPin className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                      <span>{h.address}, {h.city}, {h.country}</span>
                    </div>

                    {h.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-slate-400 shrink-0" />
                        <span className="font-semibold text-slate-800 dark:text-slate-200">{h.phone}</span>
                      </div>
                    )}
                  </div>

                  {/* Specialties tags */}
                  {h.specialties && h.specialties.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-4">
                      {h.specialties.map((s) => (
                        <span
                          key={s}
                          className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Bottom link buttons */}
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${h.name} ${h.address} ${h.city}`)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-teal-600 hover:text-teal-700 flex items-center gap-1 hover:underline"
                  >
                    <span>View on Google Maps</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>

                  {h.website && (
                    <a
                      href={h.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-slate-500 hover:text-slate-800 flex items-center gap-1 hover:underline"
                    >
                      <Globe className="w-3.5 h-3.5" />
                      <span>Official Site</span>
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
